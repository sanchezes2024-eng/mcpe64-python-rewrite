import tempfile
import unittest
from pathlib import Path

from mcpepy.world import World
from mcpepy.region_file import (
    CHUNK_BLOCK_COUNT, CHUNK_COLUMNS, NIBBLE_ARRAY_BYTES,
    NativeChunkData, RegionFile, decode_chunk_payload, encode_chunk_payload,
)


class NativeRegionFileTests(unittest.TestCase):
    def make_chunk(self, fill):
        return NativeChunkData(
            bytes([fill]) * CHUNK_BLOCK_COUNT,
            bytes([fill + 1]) * NIBBLE_ARRAY_BYTES,
            bytes([fill + 2]) * NIBBLE_ARRAY_BYTES,
            bytes([fill + 3]) * NIBBLE_ARRAY_BYTES,
            bytes([fill + 4]) * CHUNK_COLUMNS,
        )

    def test_native_payload_round_trip_uses_levelchunk_array_order(self):
        chunk = self.make_chunk(3)
        raw = encode_chunk_payload(chunk)
        self.assertEqual(decode_chunk_payload(raw), chunk)

    def test_chunks_dat_round_trip_and_sector_header(self):
        with tempfile.TemporaryDirectory() as directory:
            region = RegionFile(directory)
            self.assertTrue(region.open())
            chunk = encode_chunk_payload(self.make_chunk(9))
            region.write_chunk(2, 3, chunk)
            self.assertEqual(region.read_chunk(2, 3), chunk)
            self.assertIsNone(region.read_chunk(3, 3))
            self.assertTrue((Path(directory) / "chunks.dat").is_file())

    def test_native_chunk_blocks_load_into_world_with_matching_layout(self):
        with tempfile.TemporaryDirectory() as directory:
            region = RegionFile(directory)
            region.open()
            region.write_chunk(1, 2, encode_chunk_payload(self.make_chunk(17)))
            world = World(16, 128, 16)
            self.assertEqual(region.load_into_world(world), 1)
            self.assertEqual(world.get_block(16, 0, 32), 17)
            self.assertEqual(world.get_block(16, 127, 32), 17)

    def test_chunk_coordinates_are_bounded_to_native_region(self):
        with tempfile.TemporaryDirectory() as directory:
            region = RegionFile(directory)
            region.open()
            with self.assertRaises(ValueError):
                region.read_chunk(32, 0)

    def test_short_payload_is_rejected(self):
        with self.assertRaises(ValueError):
            decode_chunk_payload(b"short")


if __name__ == "__main__":
    unittest.main()
