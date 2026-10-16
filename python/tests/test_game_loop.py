import unittest
from mcpepy.camera import Camera
from mcpepy.game import Game
from mcpepy.math3d import Vec3

class CameraTests(unittest.TestCase):
    def test_forward_points_negative_z_at_zero_yaw(self):
        camera=Camera(Vec3(0,0,0),yaw=0,pitch=0)
        self.assertAlmostEqual(camera.forward.x,0)
        self.assertAlmostEqual(camera.forward.z,-1)

    def test_pitch_is_clamped(self):
        camera=Camera(Vec3(0,0,0),pitch=0)
        camera.rotate(0,100)
        self.assertLess(camera.pitch,1.56)

    def test_local_movement(self):
        camera=Camera(Vec3(0,0,0),yaw=0,pitch=0)
        camera.move_local(1,0)
        self.assertAlmostEqual(camera.position.z,-1)

class GameLoopTests(unittest.TestCase):
    def test_game_creates_terrain_and_frame(self):
        game=Game(48,36,seed=1)
        self.assertGreater(game.world.get_block(8,3,8),0)
        ppm=game.render()
        self.assertTrue(ppm.startswith(b"P6"))
        self.assertGreater(game.last_triangles,0)

    def test_step_updates_player_and_camera(self):
        game=Game(48,36,seed=1)
        before=game.player_z
        game.step({"w"},dt=.05)
        self.assertNotEqual(game.player_z,before)
        self.assertAlmostEqual(game.camera.position.y,game.player_y+1.55)

if __name__=="__main__":
    unittest.main()
