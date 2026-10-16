"""Optional Panda3D backend using the repository's original terrain atlas.

This is a clean-room adapter over the Python voxel model. Block UVs are selected
from data/images/terrain.png; the original atlas is used directly at runtime.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .chunkmesh import build_world_mesh
from .voxel import AIR, BEDROCK, DIRT, GRASS, STONE
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
            GeomTriangles, GeomVertexArrayFormat, GeomVertexData,
            GeomVertexFormat, GeomVertexWriter, InternalName, Texture, Vec4,
            WindowProperties,
        )
    except ImportError as exc:
        raise RuntimeError(
            "Panda3D is optional. Install it with: "
            "python3 -m pip install -r requirements-panda3d.txt"
        ) from exc
    return {
        "AmbientLight": AmbientLight, "DirectionalLight": DirectionalLight,
        "Fog": Fog, "Geom": Geom, "GeomNode": GeomNode,
        "GeomTriangles": GeomTriangles, "GeomVertexArrayFormat": GeomVertexArrayFormat,
        "GeomVertexData": GeomVertexData, "GeomVertexFormat": GeomVertexFormat,
        "GeomVertexWriter": GeomVertexWriter, "InternalName": InternalName,
        "Texture": Texture, "Vec4": Vec4, "WindowProperties": WindowProperties,
    }


class Panda3DRenderBridge:
    """Build a batched textured GeomNode from the world's exposed voxel faces."""

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
        inset = 0.5 / 256.0
        u0, u1 = col / 16.0 + inset, (col + 1) / 16.0 - inset
        v0, v1 = 1.0 - (row + 1) / 16.0 + inset, 1.0 - row / 16.0 - inset
        u, v = float(uv[0]), float(uv[1])
        return (u0 + (u1 - u0) * u, v0 + (v1 - v0) * v)

    def rebuild_world(self):
        p = self._p
        if self.node_path is not None:
            self.node_path.removeNode()

        # Explicit registered format works across Panda3D builds that lack
        # the getV3t2c4() convenience format.
        array = p["GeomVertexArrayFormat"]()
        array.addColumn(p["InternalName"].getVertex(), 3,
                        p["Geom"].NTFloat32, p["Geom"].CPoint)
        array.addColumn(p["InternalName"].getTexcoord(), 2,
                        p["Geom"].NTFloat32, p["Geom"].CTexcoord)
        array.addColumn(p["InternalName"].getColor(), 4,
                        p["Geom"].NTFloat32, p["Geom"].CColor)
        fmt = p["GeomVertexFormat"]()
        fmt.addArray(array)
        fmt = p["GeomVertexFormat"].registerFormat(fmt)
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
    """Run the Python Game model through Panda3D with classic FPS mouse look."""

    MOUSE_SENSITIVITY = 0.0025

    def __init__(self, base: Any, seed: int = 7):
        from .game import Game

        self.base = base
        self.game = Game(seed=seed)
        self.bridge = Panda3DRenderBridge(base, self.game.world)
        self.bridge.install_basic_lighting()
        base.setBackgroundColor(0.45, 0.68, 0.88, 1)
        base.camLens.setFov(70)
        self._keys = set()
        self._mouse_locked = False
        self._bind_inputs()
        self._sync_camera()
        self.base.taskMgr.add(self._tick, "mcpe-python-game-tick")

    @property
    def mouse_locked(self):
        return self._mouse_locked

    def _bind_inputs(self):
        # Shift is sneak in the original keyboard input mapping, not sprint.
        for key in ("w", "a", "s", "d", "space", "shift"):
            self.base.accept(key, self._keys.add, [key])
            self.base.accept(key + "-up", self._keys.discard, [key])
        # First left click captures the pointer. Once captured, left click
        # mines and right click places, like the original PC-style controls.
        self.base.accept("mouse1", self._left_click)
        self.base.accept("mouse3", self._right_click)
        self.base.accept("escape", self.unlock_mouse)
        self.base.accept("window-event", self._on_window_event)

    def _left_click(self):
        if not self._mouse_locked:
            self.lock_mouse()
            return
        self.break_targeted_block()

    def _right_click(self):
        if self._mouse_locked:
            self.place_targeted_block()

    def _target_block(self, reach: float = 5.0):
        """Voxel raycast from the camera; return (hit cell, previous air cell)."""
        camera = self.base.camera
        forward = camera.getQuat(self.base.render).getForward()
        # Panda coordinates are (world X, world Z, world Y).
        origin = (self.game.player_x, self.game.player_y + 1.55, self.game.player_z)
        direction = (float(forward.x), float(forward.z), float(forward.y))
        length = sum(v * v for v in direction) ** 0.5
        if length < 1e-9:
            return None
        direction = tuple(v / length for v in direction)
        from math import floor
        cell = [int(floor(v)) for v in origin]
        step = [1 if v > 0 else (-1 if v < 0 else 0) for v in direction]
        t_delta = [abs(1.0 / v) if abs(v) > 1e-9 else float("inf") for v in direction]
        t_max = []
        for axis in range(3):
            if step[axis] > 0:
                t_max.append((cell[axis] + 1 - origin[axis]) / direction[axis])
            elif step[axis] < 0:
                t_max.append((origin[axis] - cell[axis]) / -direction[axis])
            else:
                t_max.append(float("inf"))
        previous_air = None
        distance = 0.0
        while distance <= reach:
            x, y, z = cell
            try:
                block = self.game.world.get_block(x, y, z)
            except IndexError:
                block = AIR
            if block != AIR:
                return (tuple(cell), previous_air)
            previous_air = tuple(cell)
            axis = min(range(3), key=lambda i: t_max[i])
            distance = t_max[axis]
            cell[axis] += step[axis]
            t_max[axis] += t_delta[axis]
        return None

    def break_targeted_block(self):
        target = self._target_block()
        if target is None:
            return False
        (x, y, z), _ = target
        if y < 0 or y >= self.game.world.chunk_height:
            return False
        self.game.world.set_block(x, y, z, AIR)
        self.bridge.rebuild_world()
        return True

    def place_targeted_block(self):
        target = self._target_block()
        if target is None:
            return False
        (x, y, z), air_cell = target
        if air_cell is None:
            return False
        ax, ay, az = air_cell
        if ay < 0 or ay >= self.game.world.chunk_height:
            return False
        # Do not let placement put a block inside the player's collision box.
        player = self.game.player_bounds()
        if (player.min_x < ax + 1 and player.max_x > ax
                and player.min_y < ay + 1 and player.max_y > ay
                and player.min_z < az + 1 and player.max_z > az):
            return False
        self.game.world.set_block(ax, ay, az, DIRT)
        self.bridge.rebuild_world()
        return True

    def _on_window_event(self, window):
        if window is not None and not window.getProperties().getForeground():
            self.unlock_mouse()

    def lock_mouse(self):
        """Hide and recenter the cursor; click the game view to capture it."""
        if self._mouse_locked or self.base.win is None:
            return
        props = self._panda_window_properties()
        props.setCursorHidden(True)
        self.base.win.requestProperties(props)
        self._mouse_locked = True
        self._center_pointer()

    def unlock_mouse(self):
        """Release the pointer with Escape so menus/desktop remain accessible."""
        if not self._mouse_locked:
            return
        self._mouse_locked = False
        props = self._panda_window_properties()
        props.setCursorHidden(False)
        self.base.win.requestProperties(props)
        self._keys.clear()

    def _panda_window_properties(self):
        return self.bridge._p["WindowProperties"]()

    def _center_pointer(self):
        if self.base.win is None:
            return
        width, height = self.base.win.getXSize(), self.base.win.getYSize()
        if width > 0 and height > 0:
            self.base.win.movePointer(0, width // 2, height // 2)

    def _read_mouse_delta(self):
        if not self._mouse_locked or self.base.win is None:
            return 0.0, 0.0
        pointer = self.base.win.getPointer(0)
        width, height = self.base.win.getXSize(), self.base.win.getYSize()
        cx, cy = width // 2, height // 2
        dx, dy = pointer.getX() - cx, pointer.getY() - cy
        if dx or dy:
            self.base.win.movePointer(0, cx, cy)
        return float(dx), float(dy)

    def _sync_camera(self):
        camera = self.base.camera
        camera.setPos(self.game.player_x, self.game.player_z,
                      self.game.player_y + 1.55)
        camera.setH(self.game.yaw * 57.2957795 + 180.0)
        camera.setP(self.game.pitch * 57.2957795)
        camera.setR(0)

    def _tick(self, task):
        dt = min(max(task.dt, 0.0), 0.05)
        dx, dy = self._read_mouse_delta()
        # Mouse movement is a per-frame delta, unlike the game step's
        # radians-per-second look input.
        # Panda's positive horizontal pointer delta is opposite to the
        # native MCPE yaw convention used by Game.step().
        look_x = -dx * self.MOUSE_SENSITIVITY / max(dt, 1e-6)
        look_y = -dy * self.MOUSE_SENSITIVITY / max(dt, 1e-6)
        if not self._mouse_locked:
            look_x = 0.0
            look_y = 0.0
        self.game.step(self._keys, dt, look_x=look_x, look_y=look_y)
        self._sync_camera()
        return task.cont
