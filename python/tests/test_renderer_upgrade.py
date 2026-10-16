import unittest
from mcpepy.math3d import Vec3
from mcpepy.renderer import SoftwareRenderer
from mcpepy.texture import Texture

class RendererUpgradeTests(unittest.TestCase):
    def test_triangle_crossing_near_plane_is_clipped(self):
        r=SoftwareRenderer(80,60,near=.1,far=20)
        r.begin_frame(Vec3(0,0,0),Vec3(0,0,-1),(0,0,0))
        r.draw_triangle(Vec3(-.5,-.5,-.05),Vec3(.7,-.5,-1),Vec3(0,.7,-1),(255,40,20))
        self.assertIn(bytes((255,40,20)),r.framebuffer.color)

    def test_textured_triangle(self):
        r=SoftwareRenderer(64,64)
        r.begin_frame(Vec3(0,0,0),Vec3(0,0,-1),(0,0,0))
        tex=Texture.solid((25,210,70),2,2)
        r.draw_textured_triangle(Vec3(-.6,-.5,-2),Vec3(.6,-.5,-2),Vec3(0,.6,-2),((0,0),(1,0),(.5,1)),tex)
        self.assertIn(bytes((25,210,70)),r.framebuffer.color)

    def test_alpha_texture_blends(self):
        r=SoftwareRenderer(64,64)
        r.begin_frame(Vec3(0,0,0),Vec3(0,0,-1),(20,40,60))
        tex=Texture.solid((220,20,10,128))
        r.draw_textured_triangle(Vec3(-.6,-.5,-2),Vec3(.6,-.5,-2),Vec3(0,.6,-2),((0,0),(1,0),(.5,1)),tex)
        self.assertIn(bytes((120,30,35)),r.framebuffer.color)

if __name__=="__main__":
    unittest.main()
