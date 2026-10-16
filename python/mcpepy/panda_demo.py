"""Launch the optional Panda3D-backed world and MCPE-style menu flow."""
from __future__ import annotations


def main():
    try:
        from direct.showbase.ShowBase import ShowBase
    except ImportError as exc:
        raise SystemExit(
            "Panda3D is not installed. Run: "
            "python3 -m pip install -r requirements-panda3d.txt"
        ) from exc

    from .panda3d_bridge import Panda3DGameAdapter
    from .panda3d_ui import MCPE061Screens

    class MCPEPythonApp(ShowBase):
        def __init__(self):
            super().__init__()
            self.disableMouse()
            self.setWindowTitle("MCPE 0.6.1 Python/Panda3D Migration")
            self.game_adapter = None
            self.screens = MCPE061Screens(self, self.start_game)

        def start_game(self):
            self.screens.ui.clear()
            if self.game_adapter is None:
                self.game_adapter = Panda3DGameAdapter(self)
            else:
                self.game_adapter.bridge.rebuild_world()

    app = MCPEPythonApp()
    app.run()


if __name__ == "__main__":
    main()
