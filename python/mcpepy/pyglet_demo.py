"""Lightweight Pyglet/OpenGL frontend for the MCPE Python prototype.

Install with: python3 -m pip install -r requirements-pyglet.txt
Run from the python directory: python3 -m mcpepy.pyglet_demo
Pyglet 1.5 is pinned because this renderer intentionally uses compatibility
OpenGL display lists, which are simple and efficient for this small static mesh.
"""
from __future__ import annotations

import math

try:
    import pyglet
    from pyglet.gl import (
        GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_DEPTH_TEST,
        GL_MODELVIEW, GL_PROJECTION, GL_QUADS, GL_TEXTURE_2D,
        GL_CULL_FACE, GL_BACK, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER,
        GL_NEAREST, GL_RGBA, GL_UNSIGNED_BYTE, GL_UNPACK_ALIGNMENT,
        glBegin, glBindTexture, glClear, glClearColor, glColor3f, glDisable,
        glEnable, glEnd, glGenTextures, glLoadIdentity, glMatrixMode,
        glNewList, glEndList, glCallList, glTexCoord2f, glTexImage2D,
        glTexParameteri, glVertex3f, glViewport, glPixelStorei, glDeleteLists,
        glDeleteTextures, glCullFace, glClearDepth, glDepthFunc, GL_LEQUAL,
    )
    from pyglet.gl import gluPerspective, gluLookAt
    from pyglet.window import key, mouse
except ImportError as exc:
    raise SystemExit(
        "Pyglet frontend needs its optional dependencies. Run: "
        "python3 -m pip install -r requirements-pyglet.txt"
    ) from exc

from .game import Game
from .chunkmesh import build_world_mesh
from .panda3d_bridge import TERRAIN_TILES, ASSET_ROOT
from .voxel import AIR, DIRT


FACE_LIGHT = {
    "top": 1.0, "bottom": 0.52, "east": 0.82,
    "west": 0.82, "north": 0.72, "south": 0.72,
}


def _face_uvs(block_id, direction, uv):
    tiles = TERRAIN_TILES.get(block_id, {})
    tile = tiles.get(direction, tiles.get("side", tiles.get("all")))
    if tile is None:
        return uv
    col, row = tile
    inset = 0.5 / 256.0
    u0, u1 = col / 16.0 + inset, (col + 1) / 16.0 - inset
    v0, v1 = 1.0 - (row + 1) / 16.0 + inset, 1.0 - row / 16.0 - inset
    return u0 + (u1-u0)*uv[0], v0 + (v1-v0)*uv[1]


class PygletGame:
    def __init__(self):
        self.game = Game()
        self.window = pyglet.window.Window(
            width=960, height=600, caption="MCPE 0.6.1 Python — Pyglet",
            resizable=True, vsync=True,
        )
        self.keys = key.KeyStateHandler()
        self.window.push_handlers(self.keys)
        self.yaw = self.game.yaw
        self.pitch = self.game.pitch
        self.mouse_locked = False
        self.texture_id = 0
        self.mesh_list = 0
        self._load_texture()
        self.rebuild_mesh()
        self.window.push_handlers(self)
        pyglet.clock.schedule(self.update, 1.0 / 60.0)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glClearDepth(1.0)
        glClearColor(0.45, 0.68, 0.88, 1.0)

    def _load_texture(self):
        path = ASSET_ROOT / "terrain.png"
        if not path.is_file():
            return
        try:
            from PIL import Image
            image = Image.open(str(path)).convert("RGBA").transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            width, height = image.size
            data = image.tobytes()
            texture = (pyglet.gl.GLuint * 1)()
            glGenTextures(1, texture)
            self.texture_id = int(texture[0])
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0,
                         GL_RGBA, GL_UNSIGNED_BYTE, data)
        except Exception:
            self.texture_id = 0

    def rebuild_mesh(self):
        if self.mesh_list:
            glDeleteLists(self.mesh_list, 1)
        from pyglet.gl import glGenLists
        self.mesh_list = int(glGenLists(1))
        glNewList(self.mesh_list, pyglet.gl.GL_COMPILE)
        if self.texture_id:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
        else:
            glDisable(GL_TEXTURE_2D)
        glBegin(GL_QUADS)
        for face in build_world_mesh(self.game.world).faces:
            light = FACE_LIGHT.get(face.direction, 1.0)
            if not self.texture_id:
                colors = {1:(0.35,0.70,0.27),2:(0.51,0.35,0.22),
                          3:(0.47,0.47,0.47),4:(0.25,0.25,0.25)}
                base = colors.get(face.block_id, (1,0,1))
                glColor3f(base[0]*light, base[1]*light, base[2]*light)
            for vertex, uv in zip(face.vertices, face.uvs):
                if self.texture_id:
                    u, v = _face_uvs(face.block_id, face.direction, uv)
                    glTexCoord2f(u, v)
                glVertex3f(vertex.x, vertex.y, vertex.z)
        glEnd()
        glEndList()

    def on_resize(self, width, height):
        glViewport(0, 0, max(1, width), max(1, height))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(70.0, max(1, width) / max(1, height), 0.05, 96.0)
        glMatrixMode(GL_MODELVIEW)
        return pyglet.event.EVENT_HANDLED

    def on_draw(self):
        self.window.clear()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        x, y, z = self.game.player_x, self.game.player_y + 1.55, self.game.player_z
        yaw, pitch = self.game.yaw, self.game.pitch
        fx = math.sin(yaw) * math.cos(pitch)
        fy = math.sin(pitch)
        fz = -math.cos(yaw) * math.cos(pitch)
        gluLookAt(x, y, z, x+fx, y+fy, z+fz, 0, 1, 0)
        if self.texture_id:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
            glColor3f(1, 1, 1)
        glCallList(self.mesh_list)
        # Small crosshair; switch to screen-space orthographic coordinates.
        glDisable(GL_TEXTURE_2D)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        from pyglet.gl import glOrtho
        glOrtho(0, self.window.width, 0, self.window.height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        from pyglet.gl import GL_LINES
        glColor3f(1, 1, 1)
        from pyglet.gl import glLineWidth
        glLineWidth(2)
        from pyglet.gl import glBegin as _begin, glEnd as _end
        _begin(GL_LINES)
        from pyglet.gl import glVertex2f
        cx, cy = self.window.width/2, self.window.height/2
        glVertex2f(cx-6, cy); glVertex2f(cx+6, cy)
        glVertex2f(cx, cy-6); glVertex2f(cx, cy+6)
        _end()
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(70.0, max(1, self.window.width)/max(1, self.window.height), 0.05, 96.0)
        glMatrixMode(GL_MODELVIEW)

    def update(self, dt):
        dt = min(max(float(dt), 0.0), 0.05)
        pressed = set()
        for symbol, name in ((key.W, "w"), (key.A, "a"), (key.S, "s"),
                             (key.D, "d"), (key.SPACE, "space"), (key.LSHIFT, "shift")):
            if self.keys[symbol]:
                pressed.add(name)
        self.game.step(pressed, dt)
    
    def _target_block(self, reach=5.0):
        origin = (self.game.player_x, self.game.player_y+1.55, self.game.player_z)
        yaw, pitch = self.game.yaw, self.game.pitch
        direction = (math.sin(yaw)*math.cos(pitch), math.sin(pitch),
                     -math.cos(yaw)*math.cos(pitch))
        cell = [math.floor(v) for v in origin]
        step = [1 if v>0 else (-1 if v<0 else 0) for v in direction]
        delta = [abs(1/v) if abs(v)>1e-9 else float("inf") for v in direction]
        maximum = []
        for axis in range(3):
            if step[axis] > 0: maximum.append((cell[axis]+1-origin[axis])/direction[axis])
            elif step[axis] < 0: maximum.append((origin[axis]-cell[axis])/-direction[axis])
            else: maximum.append(float("inf"))
        previous = None
        distance = 0.0
        while distance <= reach:
            x,y,z = cell
            try: block = self.game.world.get_block(x,y,z)
            except IndexError: block = AIR
            if block != AIR: return tuple(cell), previous
            previous = tuple(cell)
            axis = min(range(3), key=lambda i: maximum[i])
            distance = maximum[axis]
            cell[axis] += step[axis]
            maximum[axis] += delta[axis]
        return None

    def on_mouse_press(self, x, y, button, modifiers):
        if not self.mouse_locked:
            self.mouse_locked = True
            self.window.set_exclusive_mouse(True)
            return
        target = self._target_block()
        if target is None: return
        (bx,by,bz), air = target
        if button == mouse.LEFT and 0 <= by < self.game.world.chunk_height:
            self.game.world.set_block(bx, by, bz, AIR)
            self.rebuild_mesh()
        elif button == mouse.RIGHT and air is not None:
            ax,ay,az = air
            if not 0 <= ay < self.game.world.chunk_height: return
            player = self.game.player_bounds()
            if (player.min_x < ax+1 and player.max_x > ax and
                player.min_y < ay+1 and player.max_y > ay and
                player.min_z < az+1 and player.max_z > az):
                return
            self.game.world.set_block(ax, ay, az, DIRT)
            self.rebuild_mesh()

    def on_mouse_motion(self, x, y, dx, dy):
        if not self.mouse_locked: return
        self.game.yaw -= dx * 0.0025
        self.game.pitch = max(-1.5533, min(1.5533, self.game.pitch + dy*0.0025))

    def on_key_press(self, symbol, modifiers):
        if symbol == key.ESCAPE:
            self.mouse_locked = False
            self.window.set_exclusive_mouse(False)
        elif symbol == key.SPACE:
            self.game.jump()

    def on_close(self):
        if self.mesh_list:
            glDeleteLists(self.mesh_list, 1)
        if self.texture_id:
            textures = (pyglet.gl.GLuint * 1)(self.texture_id)
            glDeleteTextures(1, textures)
        self.window.close()
        return pyglet.event.EVENT_HANDLED


def main():
    PygletGame()
    pyglet.app.run()


if __name__ == "__main__":
    main()
