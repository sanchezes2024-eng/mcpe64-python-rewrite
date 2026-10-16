import unittest

from mcpepy.math3d import Mat4, Vec3
from mcpepy.framebuffer import Framebuffer
from mcpepy.renderer import SoftwareRenderer


class MathTests(unittest.TestCase):
    def test_vector_cross_product(self):
        self.assertEqual(Vec3(1, 0, 0).cross(Vec3(0, 1, 0)), Vec3(0, 0, 1))

    def test_identity_transform(self):
        result = Mat4.identity().transform4((2, 3, 4, 1))
        self.assertEqual(result, (2, 3, 4, 1))

    def test_invalid_perspective_parameters(self):
        with self.assertRaises(ValueError):
            Mat4.perspective(70, 1, 10, 1)


class FramebufferTests(unittest.TestCase):
    def test_depth_buffer_keeps_nearest_fragment(self):
        fb = Framebuffer(2, 2, (0, 0, 0))
        self.assertTrue(fb.put_pixel(0, 0, 0.2, (255, 0, 0)))
        self.assertFalse(fb.put_pixel(0, 0, 0.8, (0, 255, 0)))
        self.assertEqual(tuple(fb.color[:3]), (255, 0, 0))

    def test_ppm_header(self):
        fb = Framebuffer(1, 1)
        self.assertTrue(fb.to_ppm().startswith(b"P6\n1 1\n255\n"))


class RendererTests(unittest.TestCase):
    def test_triangle_writes_pixels(self):
        renderer = SoftwareRenderer(64, 64)
        renderer.begin_frame(Vec3(0, 0, 0), Vec3(0, 0, -1), (0, 0, 0))
        renderer.draw_triangle(Vec3(-0.5, -0.5, -2),
                               Vec3(0.5, -0.5, -2),
                               Vec3(0, 0.5, -2), (240, 40, 20))
        self.assertIn(bytes((240, 40, 20)), renderer.framebuffer.color)


if __name__ == "__main__":
    unittest.main()
