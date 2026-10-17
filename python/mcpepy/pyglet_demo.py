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
        GL_CULL_FACE, GL_BACK, GL_POINTS, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER,
        GL_NEAREST, GL_RGBA, GL_UNSIGNED_BYTE, GL_UNPACK_ALIGNMENT,
        glBegin, glBindTexture, glClear, glClearColor, glColor3f, glDisable,
        glEnable, glEnd, glGenTextures, glLoadIdentity, glMatrixMode,
        glNewList, glEndList, glCallList, glTexCoord2f, glTexImage2D,
        glTexParameteri, glVertex3f, glViewport, glPixelStorei, glDeleteLists,
        glDeleteTextures, glCullFace, glClearDepth, glDepthFunc, glPointSize, GL_LEQUAL,
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
from .voxel import AIR, GRASS, DIRT, STONE
from .inventory import Inventory
from .particles import ParticleEngine
from .settings import load_options, save_options
from .world_storage import create_world, list_worlds


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
        self.screen = "title"
        self.menu_buttons = []
        self.world_name = "My World"
        self.worlds = list_worlds()
        self.selected_world_id = self.worlds[0].id if self.worlds else None
        self.options = load_options()
        self.previous_screen = "title"
        self.inventory = Inventory()
        self.inventory.add(DIRT, 32)
        self.inventory.add(GRASS, 32)
        self.inventory.add(STONE, 32)
        self.particles = ParticleEngine(seed=self.game.seed)
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
        self.ui_images = {}
        self._mouse_x = -1
        self._mouse_y = -1
        self._load_ui_assets()
        self._load_texture()
        self.rebuild_mesh()
        self.window.push_handlers(self)
        pyglet.clock.schedule_interval(self.update, 1.0 / 60.0)
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
        if self.screen != "playing":
            self._draw_menu()
            return
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
        if self.particles.particles:
            glDisable(GL_TEXTURE_2D)
            glPointSize(5.0)
            glBegin(GL_POINTS)
            for particle in self.particles.particles:
                fade = max(0.0, 1.0 - particle.age / particle.lifetime)
                glColor3f(particle.color[0]*fade, particle.color[1]*fade, particle.color[2]*fade)
                glVertex3f(particle.x, particle.y, particle.z)
            glEnd()
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
        self._draw_hud()
        if self.options.get("show_fps"):
            pyglet.text.Label("FPS: %d" % pyglet.clock.get_fps(),
                font_name="Arial", font_size=12, x=8, y=self.window.height-20,
                color=(255,255,255,255)).draw()

    def _draw_hud(self):
        from pyglet import shapes
        from pyglet.gl import glOrtho
        glDisable(GL_TEXTURE_2D)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.window.width, 0, self.window.height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        slot = min(48, max(30, int(min(self.window.width, self.window.height) * 0.065)))
        total = slot * 9
        start_x = (self.window.width - total) / 2
        y = 14
        names = {GRASS: "G", DIRT: "D", STONE: "S"}
        for i in range(9):
            x = start_x + i * slot
            selected = i == self.inventory.selected_hotbar
            shapes.Rectangle(x, y, slot-2, slot-2,
                color=(230, 220, 150) if selected else (25, 25, 25)).draw()
            shapes.Rectangle(x+3, y+3, slot-8, slot-8, color=(105, 105, 105)).draw()
            stack = self.inventory.slots[i]
            if stack:
                pyglet.text.Label(names.get(stack.item_id, str(stack.item_id)),
                    font_name="Arial", bold=True, font_size=max(10, slot*0.32),
                    x=x+slot/2, y=y+slot*0.58, anchor_x="center", anchor_y="center",
                    color=(255,255,255,255)).draw()
                pyglet.text.Label(str(stack.count), font_name="Arial", font_size=10,
                    x=x+slot-6, y=y+4, anchor_x="right", anchor_y="bottom",
                    color=(255,255,255,255)).draw()
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(70.0, max(1, self.window.width)/max(1, self.window.height), 0.05, 96.0)
        glMatrixMode(GL_MODELVIEW)

    def update(self, dt):
        dt = min(max(float(dt), 0.0), 0.05)
        if self.screen != "playing":
            return
        self.particles.update(dt)
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

    def _load_ui_assets(self):
        """Load original Pocket Edition GUI textures and the bundled pixel font."""
        for name in ("gui/background.png", "gui/title.png", "gui/gui.png",
                     "gui/touchgui.png", "gui/icons.png", "gui/default_world.png", "gui/logo/github.png"):
            path = ASSET_ROOT / name
            if path.is_file():
                try:
                    self.ui_images[name] = pyglet.image.load(str(path))
                except Exception:
                    pass
        font_path = ASSET_ROOT.parent / "fonts" / "minecraft.ttf"
        if font_path.is_file():
            try:
                pyglet.font.add_file(str(font_path))
            except Exception:
                pass

    def _draw_tiled_background(self):
        """Use the original gui/background.png dirt tile, like Screen.cpp."""
        from pyglet.gl import glColor4f
        image = self.ui_images.get("gui/background.png")
        if image is None:
            glClearColor(0.18, 0.18, 0.18, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)
            return
        glEnable(GL_TEXTURE_2D)
        glColor4f(0.25, 0.25, 0.25, 1.0)
        tw, th = max(1, image.width), max(1, image.height)
        for x in range(0, self.window.width + tw, tw):
            for y in range(0, self.window.height + th, th):
                image.blit(x, y)
        glColor4f(1, 1, 1, 1)
        glDisable(GL_TEXTURE_2D)

    def _draw_mc_button(self, label, action, cx, cy, bw, bh):
        """Reproduce Button::renderBg's normal/hover atlas states from gui/gui.png."""
        from pyglet.sprite import Sprite
        from pyglet.gl import glEnable, GL_BLEND, glBlendFunc, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA
        x0, y0 = cx - bw / 2, cy - bh / 2
        hovered = x0 <= self._mouse_x <= x0 + bw and y0 <= self._mouse_y <= y0 + bh
        atlas = self.ui_images.get("gui/gui.png")
        if atlas is not None and atlas.width >= 200 and atlas.height >= 106:
            state = 2 if hovered else 1
            # Button.cpp selects top-origin atlas rows 46 + state*20.
            region_y = atlas.height - (46 + state * 20) - 20
            region = atlas.get_region(0, region_y, 200, 20)
            sprite = Sprite(region, x=x0, y=y0)
            sprite.scale_x = bw / 200.0
            sprite.scale_y = bh / 20.0
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            sprite.draw()
        else:
            from pyglet import shapes
            shapes.Rectangle(x0, y0, bw, bh, color=(70, 70, 70)).draw()
        color = (255, 255, 160, 255) if hovered else (224, 224, 224, 255)
        pyglet.text.Label(label, font_name="Minecraft", font_size=max(8, int(bh * 0.34)),
            x=cx, y=cy, anchor_x="center", anchor_y="center", color=color).draw()
        self.menu_buttons.append((x0, y0, x0 + bw, y0 + bh, action))

    def _draw_title_art(self):
        """Use the original title.png at the centered scale used by StartMenuScreen.cpp."""
        from pyglet.sprite import Sprite
        image = self.ui_images.get("gui/title.png")
        if image is None:
            return
        scale = min(self.window.width, image.width) / max(1, image.width)
        sprite = Sprite(image)
        sprite.scale = scale
        sprite.x = (self.window.width - image.width * scale) / 2
        sprite.y = self.window.height - image.height * scale - 4
        sprite.draw()

    def _draw_menu(self):
        from pyglet.gl import glOrtho
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.window.width, 0, self.window.height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        w, h = self.window.width, self.window.height
        self._draw_tiled_background()
        self.menu_buttons = []
        bw, bh, gap, cx = min(330, w * 0.62), max(34, h * 0.075), max(7, h * 0.018), w / 2

        if self.screen == "title":
            # StartMenuScreen::render draws title.png at GUI y=4. Screen GUI
            # coordinates are top-origin in the C++ renderer; Pyglet is bottom-origin.
            self._draw_title_art()
            # Direct coordinate port of StartMenuScreen::setupPositions().
            # Native Screen coordinates are top-origin; this renderer is bottom-origin.
            y_base = int(h / 2 + 25)
            button_specs = (
                ("Start Game", "worlds", (w - 160) // 2, y_base - 28, 160, 24),
                ("Join Game", "join", (w - 160) // 2, y_base, 160, 24),
                # C++ centers Options using the 160px Join button width, not its own width.
                ("Options", "options", (w - 160) // 2, y_base + 30, 78, 22),
            )
            for label, action, x0, top_y, button_w, button_h in button_specs:
                self._draw_mc_button(
                    label, action, x0 + button_w / 2,
                    h - top_y - button_h / 2, button_w, button_h,
                )
            pyglet.text.Label("v0.6.1 alpha", font_name="Minecraft", font_size=10,
                x=w / 2, y=h - 62, anchor_x="center",
                color=(204, 204, 204, 255)).draw()
            copyright_text = "© Mojang AB"
            copyright_label = pyglet.text.Label(copyright_text, font_name="Minecraft",
                font_size=9, x=w - 1, y=10, anchor_x="right",
                color=(255, 255, 255, 255))
            copyright_label.draw()
            logo = self.ui_images.get("gui/logo/github.png")
            if logo is not None:
                logo.blit(2, 2)
            repo_text = "Kolyah35/minecraft-pe-0.6.1"
            pyglet.text.Label(repo_text, font_name="Minecraft", font_size=9,
                x=12, y=10, anchor_x="left",
                color=(255, 255, 255, 255)).draw()
            from pyglet import shapes
            underline_y = 10 + pyglet.font.load("Minecraft", 9).ascent
            shapes.Rectangle(12, underline_y, pyglet.font.load("Minecraft", 9).get_glyphs(repo_text)[0].advance * len(repo_text), 1,
                color=(255, 255, 255)).draw()

        elif self.screen == "worlds":
            pyglet.text.Label("Select World", font_name="Minecraft", bold=True,
                font_size=max(18, int(h * 0.04)), x=cx, y=h * 0.84,
                anchor_x="center", anchor_y="center", color=(255, 255, 255, 255)).draw()
            self.worlds = list_worlds()
            if self.worlds:
                visible = self.worlds[:5]
                for i, world in enumerate(visible):
                    label = world.name + ("  [Creative]" if world.game_type == 1 else "  [Survival]")
                    self._draw_mc_button(label, "load_world:" + world.id, cx,
                        h * 0.70 - i * (bh + gap), bw, bh)
            else:
                pyglet.text.Label("No saved worlds", font_name="Minecraft", font_size=12,
                    x=cx, y=h * 0.61, anchor_x="center", color=(220,220,220,255)).draw()
            bottom = max(h * 0.20, h * 0.70 - min(5, len(self.worlds)) * (bh + gap))
            self._draw_mc_button("Create New World", "create_world", cx, bottom, bw, bh)
            self._draw_mc_button("Back", "title", cx, bottom - bh - gap, bw, bh)

        elif self.screen == "world_selected":
            selected = next((w for w in list_worlds()
                if w.id == self.selected_world_id), None)
            selected_name = selected.name if selected else self.world_name
            pyglet.text.Label(selected_name, font_name="Minecraft", bold=True,
                font_size=max(18, int(h * 0.04)), x=cx, y=h * 0.64,
                anchor_x="center", anchor_y="center", color=(255,255,255,255)).draw()
            pyglet.text.Label("Native world metadata found.", font_name="Minecraft",
                font_size=12, x=cx, y=h * 0.55, anchor_x="center",
                color=(220,220,220,255)).draw()
            pyglet.text.Label("Chunk loading and native terrain generation are not yet ported;",
                font_name="Minecraft", font_size=10, x=cx, y=h * 0.49,
                anchor_x="center", color=(255,220,160,255)).draw()
            pyglet.text.Label("starting now uses the temporary prototype terrain.",
                font_name="Minecraft", font_size=10, x=cx, y=h * 0.46,
                anchor_x="center", color=(255,220,160,255)).draw()
            self._draw_mc_button("Start (prototype terrain)", "start_world", cx, h * 0.36, bw, bh)
            self._draw_mc_button("Back", "worlds", cx, h * 0.36-bh-gap, bw, bh)

        elif self.screen == "create":
            pyglet.text.Label("Create New World", font_name="Minecraft", bold=True,
                font_size=max(18, int(h * 0.04)), x=cx, y=h * 0.62,
                anchor_x="center", anchor_y="center", color=(255, 255, 255, 255)).draw()
            pyglet.text.Label("World name: " + self.world_name, font_name="Minecraft",
                font_size=max(12, int(h * 0.025)), x=cx, y=h * 0.52,
                anchor_x="center", anchor_y="center", color=(255, 255, 255, 255)).draw()
            self._draw_mc_button("Create World", "start_world", cx, h * 0.43, bw, bh)
            self._draw_mc_button("Back", "worlds", cx, h * 0.43-bh-gap, bw, bh)

        elif self.screen == "options":
            pyglet.text.Label("Options", font_name="Minecraft", bold=True,
                font_size=max(18, int(h * 0.04)), x=cx, y=h * 0.66,
                anchor_x="center", anchor_y="center", color=(255, 255, 255, 255)).draw()
            self._draw_mc_button("Mouse sensitivity: " + ("Low" if self.options["mouse_sensitivity"] < .0025 else "Normal" if self.options["mouse_sensitivity"] < .004 else "High"),
                "sensitivity", cx, h * 0.53, bw, bh)
            self._draw_mc_button("Invert mouse Y: " + ("On" if self.options["invert_y"] else "Off"),
                "invert_y", cx, h * 0.53-bh-gap, bw, bh)
            self._draw_mc_button("Show FPS: " + ("On" if self.options["show_fps"] else "Off"),
                "show_fps", cx, h * 0.53-2*(bh+gap), bw, bh)
            self._draw_mc_button("Back", "options_back", cx, h * 0.53-3*(bh+gap), bw, bh)

        elif self.screen == "join":
            pyglet.text.Label("Join Game", font_name="Minecraft", bold=True,
                font_size=max(18, int(h * 0.04)), x=cx, y=h * 0.62,
                anchor_x="center", anchor_y="center", color=(255,255,255,255)).draw()
            pyglet.text.Label("Multiplayer networking is not yet ported from the C++ client.",
                font_name="Minecraft", font_size=max(10, int(h * 0.022)), x=cx, y=h * 0.52,
                anchor_x="center", anchor_y="center", color=(255,255,255,255)).draw()
            self._draw_mc_button("Back", "title", cx, h * 0.41, bw, bh)

        elif self.screen == "about":
            pyglet.text.Label("Minecraft PE 0.6.1 Alpha", font_name="Minecraft", bold=True,
                font_size=max(16, int(h * 0.035)), x=cx, y=h * 0.58,
                anchor_x="center", anchor_y="center", color=(255, 255, 255, 255)).draw()
            pyglet.text.Label("Original C++ reference implementation", font_name="Minecraft",
                font_size=max(10, int(h * 0.022)), x=cx, y=h * 0.51,
                anchor_x="center", anchor_y="center", color=(255, 255, 255, 255)).draw()
            self._draw_mc_button("Back", "title", cx, h * 0.41, bw, bh)

        elif self.screen == "pause":
            pyglet.text.Label("Game menu", font_name="Minecraft", bold=True,
                font_size=max(20, int(h * 0.045)), x=cx, y=h * 0.64,
                anchor_x="center", anchor_y="center", color=(255, 255, 255, 255)).draw()
            for i, (label, action) in enumerate([
                ("Back to game", "resume"), ("Options", "pause_options"), ("Quit to title", "title")
            ]):
                self._draw_mc_button(label, action, cx, h * 0.52-i*(bh+gap), bw, bh)

        elif self.screen == "inventory":
            pyglet.text.Label("Inventory", font_name="Minecraft", bold=True,
                font_size=max(20, int(h * 0.045)), x=cx, y=h * 0.72,
                anchor_x="center", anchor_y="center", color=(255, 255, 255, 255)).draw()
            slot = min(48, max(28, int(min(w, h) * 0.07)))
            start_x = cx - 4.5 * slot
            for row in range(3):
                for col in range(9):
                    idx = 9 + row * 9 + col
                    sx, sy = start_x + col * slot, h * 0.50-row*slot
                    self._draw_inventory_slot(sx, sy, slot, idx, False)
            for col in range(9):
                sx, sy = start_x + col * slot, h * 0.50-3*slot-10
                self._draw_inventory_slot(sx, sy, slot, col, col == self.inventory.selected_hotbar)
            self._draw_mc_button("Close (E / Esc)", "resume", cx, h * 0.18, bw, bh)

    def _draw_inventory_slot(self, x, y, slot, index, selected):
        from pyglet import shapes
        from pyglet.sprite import Sprite
        frame = self.ui_images.get("gui/itemframe.png")
        if frame is not None:
            sprite = Sprite(frame, x=x, y=y)
            sprite.scale_x = (slot - 3) / max(1, frame.width)
            sprite.scale_y = (slot - 3) / max(1, frame.height)
            sprite.draw()
        else:
            shapes.Rectangle(x, y, slot-3, slot-3,
                color=(225,205,115) if selected else (55,55,55)).draw()
        stack = self.inventory.slots[index]
        if stack:
            atlas = self.ui_images.get("gui/items.png")
            pyglet.text.Label(str(stack.item_id), font_name="Minecraft", font_size=10,
                x=x+slot/2, y=y+slot/2, anchor_x="center", anchor_y="center",
                color=(255,255,255,255)).draw()
            pyglet.text.Label(str(stack.count), font_name="Minecraft", font_size=9,
                x=x+slot-6, y=y+4, anchor_x="right", anchor_y="bottom",
                color=(255,255,255,255)).draw()

    def _activate_menu_button(self, action):
        if action in ("title","worlds","create","options","about"):
            if action == "title":
                self.mouse_locked = False
                self.window.set_exclusive_mouse(False)
            self.screen = action
        elif action == "pause_options":
            self.previous_screen = "pause"
            self.screen = "options"
        elif action == "resume":
            self.screen = "playing"
            self.mouse_locked = True
            self.window.set_exclusive_mouse(True)
        elif action == "join":
            self.screen = "join"
        elif action == "create_world":
            self.screen = "create"
        elif action == "sensitivity":
            values=[0.0015,0.0025,0.004]
            current=self.options["mouse_sensitivity"]
            self.options["mouse_sensitivity"]=values[(values.index(current)+1)%len(values)] if current in values else values[0]
            save_options(self.options)
        elif action == "invert_y":
            self.options["invert_y"] = not self.options["invert_y"]
            save_options(self.options)
        elif action == "show_fps":
            self.options["show_fps"] = not self.options["show_fps"]
            save_options(self.options)
        elif action == "options_back":
            self.screen = self.previous_screen if self.previous_screen in ("pause", "title") else "title"
        elif action.startswith("load_world:"):
            self.selected_world_id = action.split(":", 1)[1]
            # The native level.dat summary is selected here. Native chunks.dat
            # decoding is a separate unfinished subsystem, so do not imply that
            # the current prototype renderer has loaded this world's terrain.
            self.world_name = next((w.name for w in list_worlds()
                if w.id == self.selected_world_id), self.selected_world_id)
            self.screen = "world_selected"
        elif action == "start_world":
            if self.screen == "create":
                summary = create_world(self.world_name, self.game.seed, 0)
                self.selected_world_id = summary.id
                self.worlds = list_worlds()
            self.screen = "playing"
            self.mouse_locked = True
            self.window.set_exclusive_mouse(True)
            self.rebuild_mesh()

    def on_mouse_press(self, x, y, button, modifiers):
        if self.screen != "playing":
            if button == mouse.LEFT:
                if self.screen == "inventory":
                    slot=min(48,max(28,int(min(self.window.width,self.window.height)*0.07)))
                    start_x=self.window.width/2-4.5*slot
                    hotbar_y=self.window.height*0.50-3*slot-10
                    if hotbar_y <= y <= hotbar_y+slot:
                        col=int((x-start_x)//slot)
                        if 0 <= col < 9:
                            self.inventory.select_hotbar(col)
                            return
                for x0,y0,x1,y1,action in reversed(self.menu_buttons):
                    if x0<=x<=x1 and y0<=y<=y1:
                        self._activate_menu_button(action)
                        return
            return
        if not self.mouse_locked:
            self.mouse_locked = True
            self.window.set_exclusive_mouse(True)
            return
        target = self._target_block()
        if target is None: return
        (bx,by,bz), air = target
        if button == mouse.LEFT and 0 <= by < self.game.world.chunk_height:
            block_id=self.game.world.get_block(bx,by,bz)
            if block_id != AIR:
                self.inventory.add(block_id,1)
                self.particles.emit_block_break(bx,by,bz,block_id)
                self.game.world.set_block(bx,by,bz,AIR)
                self.rebuild_mesh()
        elif button == mouse.RIGHT and air is not None:
            ax,ay,az=air
            if not 0 <= ay < self.game.world.chunk_height: return
            stack=self.inventory.selected
            if stack is None: return
            player=self.game.player_bounds()
            if (player.min_x < ax+1 and player.max_x > ax and
                player.min_y < ay+1 and player.max_y > ay and
                player.min_z < az+1 and player.max_z > az):
                return
            self.game.world.set_block(ax,ay,az,stack.item_id)
            self.inventory.consume_selected()
            self.rebuild_mesh()

    def on_mouse_motion(self, x, y, dx, dy):
        self._mouse_x, self._mouse_y = x, y
        if not self.mouse_locked: return
        self.game.yaw += dx * self.options["mouse_sensitivity"]
        direction = -1 if self.options.get("invert_y") else 1
        self.game.pitch = max(-1.5533, min(1.5533, self.game.pitch + direction*dy*self.options["mouse_sensitivity"]))

    def on_key_press(self, symbol, modifiers):
        if symbol == key.ESCAPE:
            if self.screen == "playing":
                self.mouse_locked = False
                self.window.set_exclusive_mouse(False)
                self.screen = "pause"
            elif self.screen in ("pause","inventory"):
                self.screen = "playing"
                self.mouse_locked = True
                self.window.set_exclusive_mouse(True)
            elif self.screen == "options" and self.previous_screen == "pause":
                self.screen = "pause"
            elif self.screen != "title":
                self.screen = "title"
            else:
                self.window.close()
        elif symbol == key.E and self.screen == "playing":
            self.screen = "inventory"
            self.mouse_locked = False
            self.window.set_exclusive_mouse(False)
        elif self.screen == "playing" and key._1 <= symbol <= key._9:
            self.inventory.select_hotbar(symbol-key._1)
        elif symbol == key.SPACE and self.screen == "playing":
            self.game.jump()
        elif self.screen == "create" and symbol == key.BACKSPACE:
            self.world_name = self.world_name[:-1]
        elif self.screen == "create" and symbol == key.ENTER:
            summary = create_world(self.world_name, self.game.seed, 0)
            self.selected_world_id = summary.id
            self.worlds = list_worlds()
            self.screen = "playing"
            self.mouse_locked = True
            self.window.set_exclusive_mouse(True)
        elif self.screen == "create" and symbol in range(key.A, key.Z+1):
            self.world_name += chr(symbol).lower()

    def on_close(self):
        if self.mesh_list:
            glDeleteLists(self.mesh_list, 1)
        if self.texture_id:
            textures = (pyglet.gl.GLuint * 1)(self.texture_id)
            glDeleteTextures(1, textures)
        return pyglet.event.EVENT_UNHANDLED


def main():
    PygletGame()
    pyglet.app.run()


if __name__ == "__main__":
    main()
