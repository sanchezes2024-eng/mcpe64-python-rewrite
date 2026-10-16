"""Smoke tests for the optional Panda3D adapter without requiring Panda3D."""
import unittest

from mcpepy.panda3d_bridge import Panda3DRenderBridge, TERRAIN_TILES
from mcpepy.panda3d_ui import MCPE061Screens, Panda3DUI


class Panda3DAdapterTests(unittest.TestCase):
    def test_optional_modules_import_without_panda3d_installed(self):
        self.assertTrue(callable(Panda3DRenderBridge))
        self.assertTrue(callable(Panda3DUI))
        self.assertTrue(callable(MCPE061Screens))

    def test_world_vertex_coordinates_convert_from_y_up_to_z_up(self):
        class Vertex:
            x, y, z = 2, 3, 5

        self.assertEqual(Panda3DRenderBridge._to_panda(Vertex()), (2.0, 5.0, 3.0))

    def test_original_terrain_atlas_tiles_are_defined_for_supported_blocks(self):
        self.assertEqual(TERRAIN_TILES[1]["top"], (0, 0))
        self.assertEqual(TERRAIN_TILES[1]["side"], (3, 0))
        self.assertEqual(TERRAIN_TILES[2]["all"], (2, 0))
        self.assertEqual(TERRAIN_TILES[3]["all"], (1, 0))
        self.assertEqual(TERRAIN_TILES[4]["all"], (1, 1))

    def test_renderer_uses_a_portable_custom_vertex_format(self):
        from pathlib import Path
        source = (Path(__file__).resolve().parents[1] / "mcpepy" /
                  "panda3d_bridge.py").read_text()
        self.assertIn("GeomVertexArrayFormat", source)
        self.assertIn("InternalName.getTexcoord()", source)
        self.assertIn("InternalName.getColor()", source)

    def test_slider_reads_value_from_directslider_instance(self):
        from pathlib import Path
        source = (Path(__file__).resolve().parents[1] / "mcpepy" /
                  "panda3d_ui.py").read_text()
        self.assertIn('command=lambda: command(item["value"])', source)

    def test_mouse_look_uses_capture_and_escape_releases_pointer(self):
        from pathlib import Path
        source = (Path(__file__).resolve().parents[1] / "mcpepy" /
                  "panda3d_bridge.py").read_text()
        self.assertIn('self.base.accept("mouse1", self._left_click)', source)
        self.assertIn('self.base.accept("mouse3", self._right_click)', source)
        self.assertIn('self.base.accept("escape", self.unlock_mouse)', source)
        self.assertIn("setCursorHidden(True)", source)
        self.assertIn("movePointer(0, cx, cy)", source)
        self.assertIn("look_x = -dx * self.MOUSE_SENSITIVITY", source)
        self.assertIn("def break_targeted_block(self):", source)
        self.assertIn("def place_targeted_block(self):", source)

    def test_atlas_uvs_stay_inside_selected_tile(self):
        u, v = Panda3DRenderBridge._atlas_uv(1, "top", (0.5, 0.5))
        self.assertGreater(u, 0 / 16)
        self.assertLess(u, 1 / 16)
        self.assertGreater(v, 15 / 16)
        self.assertLess(v, 1.0)


if __name__ == "__main__":
    unittest.main()
