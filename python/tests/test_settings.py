"""Unit tests for persistent user options."""
import json
import os
import tempfile
import unittest
from pathlib import Path

from mcpepy.settings import DEFAULT_OPTIONS, load_options, save_options


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        os.environ["MCPEPY_CONFIG_DIR"] = self.tempdir.name

    def tearDown(self):
        os.environ.pop("MCPEPY_CONFIG_DIR", None)
        self.tempdir.cleanup()

    def test_missing_file_uses_defaults(self):
        self.assertEqual(load_options(), DEFAULT_OPTIONS)

    def test_options_round_trip(self):
        options = {
            "mouse_sensitivity": 0.004,
            "invert_y": True,
            "show_fps": True,
        }
        save_options(options)
        self.assertEqual(load_options(), options)
        self.assertTrue(Path(self.tempdir.name, "options.json").is_file())

    def test_invalid_sensitivity_is_rejected(self):
        with self.assertRaises(ValueError):
            save_options({"mouse_sensitivity": 100})

    def test_corrupt_file_falls_back_to_defaults(self):
        Path(self.tempdir.name, "options.json").write_text("{", encoding="utf-8")
        self.assertEqual(load_options(), DEFAULT_OPTIONS)


if __name__ == "__main__":
    unittest.main()
