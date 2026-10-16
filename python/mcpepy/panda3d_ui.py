"""Clean-room MCPE-style UI adapter using the repository's original GUI images."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
GUI_ASSETS = ROOT / "data" / "images" / "gui"


def _directgui():
    try:
        from direct.gui.DirectGui import (
            DirectButton, DirectCheckButton, DirectEntry, DirectFrame,
            DirectLabel, DirectSlider,
        )
    except ImportError as exc:
        raise RuntimeError(
            "Panda3D is optional. Install it with: "
            "python3 -m pip install -r requirements-panda3d.txt"
        ) from exc
    return {
        "Button": DirectButton, "CheckButton": DirectCheckButton,
        "Entry": DirectEntry, "Frame": DirectFrame, "Label": DirectLabel,
        "Slider": DirectSlider,
    }


class Panda3DUI:
    """Small DirectGUI surface with original MCPE background/logo assets."""

    def __init__(self, base: Any):
        self.base = base
        self._gui = _directgui()
        self.widgets: list[Any] = []
        self.screen_name = ""
        self.background = None

    def clear(self):
        for widget in self.widgets:
            widget.destroy()
        self.widgets.clear()
        self.background = None

    def begin_screen(self, name: str, *, title: str | None = None,
                     use_background: bool = True):
        self.clear()
        self.screen_name = name
        if use_background:
            bg = GUI_ASSETS / "background.png"
            if bg.is_file():
                # This is the game's own pixel-art menu background, not a
                # generated solid-color panel. Keep nearest-neighbor sampling.
                texture = self.base.loader.loadTexture(str(bg))
                if texture is not None:
                    from panda3d.core import Texture
                    texture.setMinfilter(Texture.FTNearest)
                    texture.setMagfilter(Texture.FTNearest)
                self.background = self._gui["Frame"](
                    parent=self.base.aspect2d,
                    frameSize=(-1.78, 1.78, -1, 1),
                    frameColor=(1, 1, 1, 1), image=texture or str(bg),
                    image_scale=(3.56, 1, 2.0), image_pos=(0, 0, 0))
                self.background.setBin("background", 0)
                self.widgets.append(self.background)
        if title:
            self.label(title, 0, 0.66, scale=0.085)
        return self

    def label(self, text: str, x: float, z: float, *, scale: float = 0.06,
              color=(1, 1, 1, 1)):
        item = self._gui["Label"](
            parent=self.base.aspect2d, text=text, pos=(x, 0, z),
            scale=scale, text_fg=color, frameColor=(0, 0, 0, 0),
            text_shadow=(0, 0, 0, 0.8), text_align=0)
        self.widgets.append(item)
        return item

    def button(self, text: str, x: float, z: float,
               command: Callable[[], Any], *, width: float = 0.72):
        item = self._gui["Button"](
            parent=self.base.aspect2d, text=text, pos=(x, 0, z),
            scale=0.06, command=command, text_scale=0.9,
            frameSize=(-width, width, -0.42, 0.42),
            frameColor=(0.18, 0.18, 0.18, 0.96),
            relief=1, text_fg=(1, 1, 1, 1),
            pressEffect=True)
        self.widgets.append(item)
        return item

    def entry(self, initial: str, x: float, z: float, *, width: int = 16,
              command: Callable[[str], Any] | None = None):
        item = self._gui["Entry"](
            parent=self.base.aspect2d, initialText=initial, pos=(x, 0, z),
            scale=0.06, width=width, command=command,
            frameColor=(0.12, 0.12, 0.12, 0.95), text_fg=(1, 1, 1, 1))
        self.widgets.append(item)
        return item

    def checkbox(self, text: str, x: float, z: float,
                 command: Callable[[bool], Any], *, checked: bool = False):
        item = self._gui["CheckButton"](
            parent=self.base.aspect2d, text=text, pos=(x, 0, z),
            scale=0.055, indicatorValue=int(checked), command=command,
            text_fg=(1, 1, 1, 1))
        self.widgets.append(item)
        return item

    def slider(self, text: str, x: float, z: float, command: Callable[[float], Any],
               *, value: float = 0.5, minimum: float = 0, maximum: float = 1):
        self.label(text, x, z + 0.09, scale=0.045)
        item = self._gui["Slider"](
            parent=self.base.aspect2d, pos=(x, 0, z - 0.04),
            value=value, range=(minimum, maximum), pageSize=(maximum-minimum)/20,
            command=command, scale=0.55)
        self.widgets.append(item)
        return item

    def image(self, filename: str, x: float, z: float, scale: float = 0.3):
        path = GUI_ASSETS / filename
        if not path.is_file():
            return None
        texture = self.base.loader.loadTexture(str(path))
        if texture is not None:
            from panda3d.core import Texture
            texture.setMinfilter(Texture.FTNearest)
            texture.setMagfilter(Texture.FTNearest)
        item = self._gui["Frame"](
            parent=self.base.aspect2d, frameSize=(-scale, scale, -scale, scale),
            frameColor=(1, 1, 1, 1), image=texture or str(path),
            image_scale=(2 * scale, 1, 2 * scale), pos=(x, 0, z))
        item.setTransparency(True)
        self.widgets.append(item)
        return item


class MCPE061Screens:
    """Initial screen flow with original MCPE title and background images."""

    def __init__(self, base: Any, start_game: Callable[[], Any]):
        self.base = base
        self.ui = Panda3DUI(base)
        self.start_game = start_game
        self.world_name = "My World"
        self.world_seed = "7"
        self.ui_main_menu()

    def ui_main_menu(self):
        # The title.png already contains the original logo; don't print a
        # second, unrelated text title over it.
        self.ui.begin_screen("main_menu", use_background=True)
        self.ui.image("title.png", 0, 0.43, 0.60)
        self.ui.button("Singleplayer", 0, 0.02, self.ui_world_select)
        self.ui.button("Options", 0, -0.13, self.ui_options)
        self.ui.button("Quit", 0, -0.28, self.base.userExit)

    def ui_world_select(self):
        self.ui.begin_screen("world_select", title="Select World")
        self.ui.image("default_world.png", -0.9, 0.18, 0.16)
        self.ui.label("Choose a world", 0, 0.34, scale=0.05)
        self.ui.button("Create New World", 0, 0.12, self.ui_create_world)
        self.ui.button("Play test terrain", 0, -0.04, self.start_game)
        self.ui.button("Back", 0, -0.25, self.ui_main_menu)

    def ui_create_world(self):
        self.ui.begin_screen("create_world", title="Create New World")
        self.ui.label("World name", -0.65, 0.28, scale=0.05)
        name = self.ui.entry(self.world_name, 0.1, 0.28)
        self.ui.label("Seed", -0.65, 0.08, scale=0.05)
        seed = self.ui.entry(self.world_seed, 0.1, 0.08)

        def create():
            self.world_name = name.get()
            self.world_seed = seed.get()
            self.start_game()

        self.ui.button("Create World", 0, -0.13, create)
        self.ui.button("Back", 0, -0.29, self.ui_world_select)

    def ui_options(self):
        self.ui.begin_screen("options", title="Options")
        self.ui.label("Field of view", 0, 0.35, scale=0.05)
        self.ui.slider("Field of view", 0, 0.12,
                       lambda value: self.base.camLens.setFov(55 + value * 45),
                       value=1/3)
        self.ui.button("Back", 0, -0.22, self.ui_main_menu)
