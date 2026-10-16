"""Optional Panda3D backend for the clean-room MCPE-style Python engine.

This is an adapter between the Python world's block/face model and Panda3D's
scene graph. Native MCPE APIs are not emulated automatically: each native
subsystem still needs an explicit, tested adapter or a clean-room replacement.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .chunkmesh import build_world_mesh
from .voxel import BEDROCK, DIRT, GRASS, STONE
from .world import World, generate_terrain_chunk

ROOT = Path(__file__).resolve().parents[2]
ASSET_ROOT = ROOT / "data" / "images"


def _panda():
    """Import Panda3D lazily so the software backend remains dependency-free."""
    try:
        from panda3d.core import (
            AmbientLight, DirectionalLight, Fog, Geom, GeomNode,
            GeomTriangles, GeomVertexData, GeomVertexFormat,
            GeomVertexWriter, NodePath, Vec4,
        )
    except ImportError as exc:
        raise RuntimeError(
            "Panda3D is optional. Install it with: "
            "python3 -m pip install -r requirements-panda3d.txt"
        ) from exc
    return {
        "AmbientLight": AmbientLight, "DirectionalLight": DirectionalLight,
        "Fog": Fog, "Geom": Geom, "GeomNode": GeomNode,
        "GeomTriangles": GeomTriangles, "GeomVertexData": GeomVertexData,
        "GeomVertexFormat": GeomVertexFormat, "GeomVertexWriter": GeomVertexWriter,
        "NodePath": NodePath, "Vec4": Vec4,
    }


class Panda3DRenderBridge:
    """Convert exposed voxel quads into a batched Panda3D GeomNode.

    The Python world uses Y-up coordinates; Panda3D's default is Z-up, so
    vertices are converted from (x, y, z) to (x, z, y). Colors are a temporary
    fallback until the original atlas's per-block UV table is implemented.
    """

    PALETTE = {
        GRASS: (0.35, 0.70, 0.27),
        DIRT: (0.51, 0.35, 0.22),
        STONE: (0.47, 0.47, 0.47),
        BEDROCK: (0.25, 0.25, 0.25),
    }
    FACE_LIGHT = {
        "top": 1.0, "bottom": 0.48, "east": 0.82,
        "west": 0.82, "north": 0.72, "south": 0.72,
    }

    def __init__(self, base: Any, world: World):
        self.base = base
        self.world = world
        self._p = _panda()
        self.node_path = None
        self.triangle_count = 0
        self.rebuild_world()

    @staticmethod
    def _to_panda(vertex):
        return (float(vertex.x), float(vertex.z), float(vertex.y))

    def rebuild_world(self):
        p = self._p
        if self.node_path is not None:
            self.node_path.removeNode()

        fmt = p["GeomVertexFormat"].getV3c4()
        data = p["GeomVertexData"]("mcpe-world", fmt, p["Geom"].UHStatic)
        vertices = p["GeomVertexWriter"](data, "vertex")
        colors = p["GeomVertexWriter"](data, "color")
        tris = p["GeomTriangles"](p["Geom"].UHStatic)
        faces = build_world_mesh(self.world).faces
        index = 0
        for face in faces:
            base = self.PALETTE.get(face.block_id, (0.75, 0.15, 0.75))
            light = self.FACE_LIGHT.get(face.direction, 1.0)
            rgba = tuple(max(0.0, min(1.0, c * light)) for c in base) + (1.0,)
            for vertex in face.vertices:
                vertices.addData3f(*self._to_panda(vertex))
                colors.addData4f(*rgba)
            tris.addVertices(index, index + 1, index + 2)
            tris.closePrimitive()
            tris.addVertices(index, index + 2, index + 3)
            tris.closePrimitive()
            index += 4

        geom = p["Geom"](data)
        geom.addPrimitive(tris)
        node = p["GeomNode"]("mcpe-voxel-world")
        node.addGeom(geom)
        self.node_path = self.base.render.attachNewNode(node)
        # Face winding differs after coordinate-system conversion; two-sided
        # rendering keeps the bridge robust while culling is not yet optimized.
        self.node_path.setTwoSided(True)
        self.triangle_count = len(faces) * 2
        return self.node_path

    def install_basic_lighting(self):
        p = self._p
        ambient = p["AmbientLight"]("mcpe-ambient")
        ambient.setColor(p["Vec4"](0.72, 0.72, 0.72, 1))
        self.base.render.setLight(self.base.render.attachNewNode(ambient))
        sun = p["DirectionalLight"]("mcpe-sun")
        sun.setColor(p["Vec4"](0.62, 0.62, 0.62, 1))
        sun_path = self.base.render.attachNewNode(sun)
        sun_path.setHpr(-35, -55, 0)
        self.base.render.setLight(sun_path)
        fog = p["Fog"]("mcpe-distance-fog")
        fog.setColor(0.45, 0.68, 0.88)
        fog.setExpDensity(0.012)
        self.base.render.setFog(fog)

    def remove(self):
        if self.node_path is not None:
            self.node_path.removeNode()
            self.node_path = None


class Panda3DGameAdapter:
    """Run the existing Python Game model through Panda3D instead of CPU pixels.

    This first adapter shares the world model, terrain generator, collision
    model, and Game.step input contract. It intentionally does not claim native
    MCPE parity or texture-atlas parity yet.
    """

    def __init__(self, base: Any, seed: int = 7):
        from .game import Game

        self.base = base
        self.game = Game(seed=seed)
        self.bridge = Panda3DRenderBridge(base, self.game.world)
        self.bridge.install_basic_lighting()
        base.setBackgroundColor(0.45, 0.68, 0.88, 1)
        base.camLens.setFov(70)
        self._keys = set()
        self._bind_inputs()
        self._sync_camera()
        self.base.taskMgr.add(self._tick, "mcpe-python-game-tick")

    def _bind_inputs(self):
        for key in ("w", "a", "s", "d", "space", "shift", "arrow_left",
                    "arrow_right", "arrow_up", "arrow_down"):
            self.base.accept(key, self._keys.add, [key])
            self.base.accept(key + "-up", self._keys.discard, [key])
        self.base.accept("escape", self.base.userExit)

    def _sync_camera(self):
        camera = self.base.camera
        # World (x,y,z) -> Panda (x,z,y); camera eye is player eye height.
        camera.setPos(self.game.player_x, self.game.player_z,
                      self.game.player_y + 1.55)
        camera.setH(self.game.yaw * 57.2957795 + 180.0)
        camera.setP(self.game.pitch * 57.2957795)
        camera.setR(0)

    def _tick(self, task):
        dt = min(max(task.dt, 0.0), 0.05)
        look_x = (1 if "arrow_right" in self._keys else 0) - (
            1 if "arrow_left" in self._keys else 0)
        look_y = (1 if "arrow_down" in self._keys else 0) - (
            1 if "arrow_up" in self._keys else 0)
        self.game.step(self._keys, dt, look_x=look_x * 1.8, look_y=look_y * 1.4)
        self._sync_camera()
        return task.cont
