import os
import tempfile
import unittest
from pathlib import Path

from mcpepy.world_storage import (
    create_world, list_worlds, read_level_dat, unique_level_id, worlds_path,
)


class NativeWorldStorageTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_create_writes_native_wrapped_nbt_metadata(self):
        world = create_world("Test World", seed=12345, game_type=0, root=self.root)
        loaded = read_level_dat(self.root / world.id)
        self.assertIsNotNone(loaded)
        version, data = loaded
        self.assertEqual(version, 2)
        self.assertEqual(data["RandomSeed"], 12345)
        self.assertEqual(data["GameType"], 0)
        self.assertEqual(data["LevelName"], "Test World")
        self.assertEqual(data["SpawnY"], 64)
        self.assertEqual(data["StorageVersion"], 2)
        self.assertEqual(data["Platform"], 2)

    def test_world_list_ignores_folders_without_level_data(self):
        (self.root / "not-a-world").mkdir()
        created = create_world("Saved", seed=7, game_type=1, root=self.root)
        worlds = list_worlds(self.root)
        self.assertEqual([item.id for item in worlds], [created.id])
        self.assertEqual(worlds[0].name, "Saved")
        self.assertEqual(worlds[0].game_type, 1)

    def test_native_unique_name_rule_appends_hyphens(self):
        create_world("World", seed=1, game_type=0, root=self.root)
        create_world("World", seed=2, game_type=0, root=self.root)
        self.assertEqual(unique_level_id("World", list_worlds(self.root)), "World--")

    def test_illegal_name_characters_are_removed(self):
        created = create_world('a/b:"c', seed=1, game_type=0, root=self.root)
        self.assertEqual(created.id, "abc")

    def test_empty_or_invalid_world_directory_is_not_listed(self):
        (self.root / "broken").mkdir()
        (self.root / "broken" / "level.dat").write_bytes(b"bad")
        self.assertEqual(list_worlds(self.root), [])


if __name__ == "__main__":
    unittest.main()
