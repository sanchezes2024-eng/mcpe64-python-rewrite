import unittest

from mcpepy.voxel import AIR, DIRT, GRASS, STONE
from mcpepy.world import World, generate_terrain_chunk


class WorldTests(unittest.TestCase):
    def test_world_coordinates_cross_chunk_edges(self):
        world = World(chunk_width=4, chunk_height=8, chunk_depth=4)
        world.set_block(4, 2, 0, GRASS)
        world.set_block(-1, 2, 0, DIRT)
        self.assertEqual(world.get_block(4, 2, 0), GRASS)
        self.assertEqual(world.get_block(-1, 2, 0), DIRT)
        self.assertEqual(len(world.chunks), 2)

    def test_empty_chunks_read_as_air(self):
        world = World(chunk_width=4, chunk_height=8, chunk_depth=4)
        self.assertEqual(world.get_block(100, 1, -100), AIR)
        self.assertEqual(len(world.chunks), 0)

    def test_visible_faces_hide_shared_chunk_boundary(self):
        world = World(chunk_width=1, chunk_height=1, chunk_depth=1)
        world.set_block(0, 0, 0, STONE)
        world.set_block(1, 0, 0, STONE)
        faces = list(world.visible_faces())
        self.assertEqual(len(faces), 10)
        self.assertFalse(any(face.x == 0 and face.direction == "east" for face in faces))
        self.assertFalse(any(face.x == 1 and face.direction == "west" for face in faces))

    def test_terrain_generation_is_deterministic(self):
        first_world = World(8, 24, 8)
        second_world = World(8, 24, 8)
        first = generate_terrain_chunk(first_world, -1, 2, seed=123, base_height=8, amplitude=3)
        second = generate_terrain_chunk(second_world, -1, 2, seed=123, base_height=8, amplitude=3)
        self.assertEqual(first.blocks, second.blocks)
        self.assertGreater(first.count_non_air(), 0)

    def test_terrain_height_validation(self):
        world = World(8, 8, 8)
        with self.assertRaises(ValueError):
            generate_terrain_chunk(world, 0, 0, base_height=8)


if __name__ == "__main__":
    unittest.main()
