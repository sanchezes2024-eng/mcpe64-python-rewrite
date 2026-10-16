import unittest

from mcpepy.physics import AABB, collides, move_and_collide
from mcpepy.voxel import STONE
from mcpepy.world import World


class PhysicsTests(unittest.TestCase):
    def test_aabb_translation(self):
        box = AABB(0, 1, 0, 1, 3, 1).translated(2, -1, 4)
        self.assertEqual(box, AABB(2, 0, 4, 3, 2, 5))

    def test_empty_space_does_not_collide(self):
        world = World(4, 8, 4)
        self.assertFalse(collides(world, AABB(0.1, 1, 0.1, 0.9, 2, 0.9)))

    def test_block_stops_horizontal_movement(self):
        world = World(4, 8, 4)
        world.set_block(1, 1, 0, STONE)
        result = move_and_collide(world, AABB(0.1, 1, 0.1, 0.9, 2, 0.9), 1.0, 0, 0)
        self.assertTrue(result.collided_x)
        self.assertAlmostEqual(result.bounds.max_x, 1.0)

    def test_floor_stops_downward_movement(self):
        world = World(4, 8, 4)
        world.set_block(0, 0, 0, STONE)
        result = move_and_collide(world, AABB(0.1, 1.1, 0.1, 0.9, 2.1, 0.9), 0, -0.5, 0)
        self.assertTrue(result.collided_y)
        self.assertTrue(result.grounded)
        self.assertAlmostEqual(result.bounds.min_y, 1.0)


if __name__ == "__main__":
    unittest.main()
