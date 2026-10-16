"""Optional Panda3D backend using the repository's original terrain atlas.

This is a clean-room adapter over the Python voxel model. Block UVs are selected
from data/images/terrain.png; the original atlas is used directly at runtime.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .chunkmesh import build_world_mesh
from .voxel import BEDROCK, DIRT, GRASS, STONE
from .world import World

ROOT = Path(__file__).resolve().parents[2]
ASSET_ROOT = ROOT / "data" / "images"

# Original MCPE terrain atlas is a 16-by-16 grid of 16-pixel tiles.
# Coordinates are (column, row), counted from the top-left of terrain.png.
# Grass uses different tiles on its top and sides.
TERRAIN_TILES = {
    GRASS: {"top": (0, 0), "bottom": (2, 0), "side": (3, 0)},
    DIRT: {"all": (2, 0)},
    STONE: {"all": (1, 0)},
    BEDROCK: {"all": (1, 1)},
}


def _panda():
    """Import Panda3D lazily so the software backend stays dependency-free."""
    try:
        from panda3d.core import (
            AmbientLight, DirectionalLight, Fog, Geom, GeomNode,
            GeomTriangles, GeomVertexData, GeomVertexFormat,
            GeomVertexWriter, Texture, Vec4,
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
        "Texture": Texture, "Vec4": Vec4,
    }


class Panda3DRenderBridge:
    """Build a batched textured GeomNode from the world's exposed voxel faces."""

    # Subtle face shading preserves the original pixel art instead of replacing
    # it with the flat placeholder colors used by the first bridge iteration.
    FACE_LIGHT = {
        "top": 1.0, "bottom": 0.52, "east": 0.82,
        "west": 0.82, "north": 0.72, "south": 0.72,
    }

    def __init__(self, base: Any, world: World):
        self.base = base
        self.world = world
        self._p = _panda()
        self.node_path = None
        self.triangle_count = 0
        self.texture = self._load_terrain_texture()
        self.rebuild_world()

    def _load_terrain_texture(self):
        """Load the real terrain atlas; keep a clear fallback if it is absent."""
        path = ASSET_ROOT / "terrain.png"
        if not path.is_file():
            return None
        try:
            texture = self.base.loader.loadTexture(str(path))
            if texture is not None:
                texture.setMinfilter(self._p["Texture"].FTNearest)
                texture.setMagfilter(self._p["Texture"].FTNearest)
                texture.setWrapU(self._p["Texture"].WMBorderColor)
                texture.setWrapV(self._p["Texture"].WMBorderColor)
            return texture
        except Exception:
            # The renderer remains launchable when assets are missing or a
            # graphics backend cannot decode them; the repository path is
            # reported through has_terrain_texture for diagnostics.
            return None

    @property
    def has_terrain_texture(self) -> bool:
        return self.texture is not None

    @staticmethod
    def _to_panda(vertex):
        # Prototype world uses Y-up; Panda3D defaults to Z-up.
        return (float(vertex.x), float(vertex.z), float(vertex.y))

    @staticmethod
    def _tile_for(block_id: int, direction: str):
        tiles = TERRAIN_TILES.get(block_id)
        if not tiles:
            return None
        if direction == "top" and "top" in tiles:
            return tiles["top"]
        if direction == "bottom" and "bottom" in tiles:
            return tiles["bottom"]
        return tiles.get("side", tiles.get("all"))

    @classmethod
    def _atlas_uv(cls, block_id: int, direction: str, uv):
        tile = cls._tile_for(block_id, direction)
        if tile is None:
            return float(uv[0]), float(uv[1])
        col, row = tile
        # A half-texel inset prevents adjacent atlas tiles bleeding together
        # when a window is resized. V is inverted because atlas rows count down.
        inset = 0.5 / 256.0
        u0, u1 = col / 16.0 + inset, (col + 1) / 16.0 - inset
        v0, v1 = 1.0 - (row + 1) / 16.0 + inset, 1.0 - row / 16.0 - inset
        u, v = float(uv[0]), float(uv[1])
        return (u0 + (u1 - u0) * u, v0 + (v1 - v0) * v)

    def rebuild_world(self):
        p = self._p
        if self.node_path is not None:
            self.node_path.removeNode()

        fmt = p["GeomVertexFormat"].getV3t2c4()
        data = p["GeomVertexData"]("mcpe-world", fmt, p["Geom"].UHStatic)
        vertices = p["GeomVertexWriter"](data, "vertex")
        texcoords = p["GeomVertexWriter"](data, "texcoord")
        colors = p["GeomVertexWriter"](data, "color")
        tris = p["GeomTriangles"](p["Geom"].UHStatic)
        faces = build_world_mesh(self.world).faces
        index = 0

        for face in faces:
            light = self.FACE_LIGHT.get(face.direction, 1.0)
            rgba = (light, light, light, 1.0)
            for vertex, uv in zip(face.vertices, face.uvs):
                vertices.addData3f(*self._to_panda(vertex))
                texcoords.addData2f(*self._atlas_uv(face.block_id, face.direction, uv))
                colors.addData4f(*rgba)
            tris.addVertices(index, index + 1, index + 2)
            tris.closePrimitive()
            tris.addVertices(index, index + 2, index + 3)
            tris.closePrimitive()
            index += 4

        geom = p["Geom"](data)
        geom.addPrimitive(tris)
        node = p["GeomNode"]("mcpe-textured-voxel-world")
        node.addGeom(geom)
        self.node_path = self.base.render.attachNewNode(node)
        self.node_path.setTwoSided(True)
        if self.texture is not None:
            self.node_path.setTexture(self.texture, 1)
        else:
            # Textures are preferred, but missing assets should not crash.
            self.node_path.setColor(0.65, 0.65, 0.65, 1.0)
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
    """Run the existing Python Game model through Panda3D."""

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
