import unittest

from mcpepy.voxel import AIR, DIRT, GRASS, STONE, Chunk, generate_flat_chunk


class ChunkTests(unittest.TestCase):
    def test_set_get_and_bounds(self):
        chunk = Chunk(2, 3, 4)
        chunk.set(1, 2, 3, GRASS)
        self.assertEqual(chunk.get(1, 2, 3), GRASS)
        with self.assertRaises(IndexError):
            chunk.get(2, 0, 0)

    def test_fill_and_non_air_count(self):
        chunk = Chunk(2, 2, 2)
        chunk.fill(STONE)
        self.assertEqual(chunk.count_non_air(), 8)
        chunk.set(0, 0, 0, AIR)
        self.assertEqual(chunk.count_non_air(), 7)

    def test_adjacent_solid_blocks_hide_internal_faces(self):
        chunk = Chunk(2, 1, 1)
        chunk.set(0, 0, 0, STONE)
        chunk.set(1, 0, 0, DIRT)
        faces = list(chunk.visible_faces())
        self.assertEqual(len(faces), 10)
        self.assertFalse(any(f.x == 0 and f.direction == "east" for f in faces))
        self.assertFalse(any(f.x == 1 and f.direction == "west" for f in faces))

    def test_flat_chunk_has_grass_top_and_dirt_under_it(self):
        chunk = generate_flat_chunk(width=3, height=8, depth=2, ground_y=3)
        self.assertEqual(chunk.get(0, 3, 0), GRASS)
        self.assertEqual(chunk.get(0, 2, 0), DIRT)
        self.assertEqual(chunk.get(0, 1, 0), STONE)
        self.assertEqual(chunk.count_non_air(), 3 * 2 * 4)

    def test_invalid_ground_height(self):
        with self.assertRaises(ValueError):
            generate_flat_chunk(height=8, ground_y=8)


if __name__ == "__main__":
    unittest.main()
