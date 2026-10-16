import tempfile
import unittest
from pathlib import Path
from mcpepy.texture import Texture

class TextureTests(unittest.TestCase):
    def test_nearest_sampling_and_clamping(self):
        tex=Texture(2,1,bytes((255,0,0,0,255,0)),3)
        self.assertEqual(tex.sample(.1,0),(255,0,0,255))
        self.assertEqual(tex.sample(.9,0),(0,255,0,255))
        self.assertEqual(tex.sample(-5,4),(255,0,0,255))

    def test_bilinear_sampling(self):
        tex=Texture(2,2,bytes((0,0,0,255,0,0,0,0,255,255,255,255)),3)
        self.assertEqual(tex.sample(.5,.5,bilinear=True),(128,64,128,255))

    def test_ppm_ascii_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"tiny.ppm"
            p.write_bytes(b"P3\n# test\n2 1\n255\n255 0 0 0 255 0\n")
            tex=Texture.load(p)
            self.assertEqual(tex.sample(.1,0),(255,0,0,255))
            self.assertEqual(tex.sample(.9,0),(0,255,0,255))

    def test_ppm_binary_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"tiny.ppm"
            p.write_bytes(b"P6\n1 1\n255\n"+bytes((3,4,5)))
            self.assertEqual(Texture.load(p).sample(0,0),(3,4,5,255))

    def test_alpha_zero_does_not_write_depth(self):
        from mcpepy.framebuffer import Framebuffer
        fb=Framebuffer(1,1,(10,20,30))
        self.assertFalse(fb.put_pixel(0,0,.1,(255,0,0),alpha=0))
        self.assertEqual(fb.depth[0],float("inf"))

if __name__=="__main__":
    unittest.main()
