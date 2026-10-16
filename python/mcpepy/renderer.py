"""Simple CPU triangle renderer. No third-party graphics package is required.

This initial version deliberately does not claim complete OpenGL ES compatibility:
homogeneous clipping and perspective-correct attributes are planned follow-up work.
"""
from __future__ import annotations
import math
from .math3d import Mat4, Vec3
from .framebuffer import Framebuffer


class SoftwareRenderer:
    def __init__(self, width=640, height=400, fov_y=70.0, near=0.05, far=128.0):
        self.width, self.height = int(width), int(height)
        self.fov_y, self.near, self.far = fov_y, near, far
        self.framebuffer = Framebuffer(self.width, self.height)
        self.projection = Mat4.perspective(fov_y, self.width / self.height, near, far)
        self.view = Mat4.identity()

    def resize(self, width: int, height: int) -> None:
        if width < 1 or height < 1:
            raise ValueError("render dimensions must be positive")
        self.width, self.height = int(width), int(height)
        self.framebuffer = Framebuffer(self.width, self.height)
        self.projection = Mat4.perspective(
            self.fov_y, self.width / self.height, self.near, self.far)

    def begin_frame(self, eye: Vec3, target: Vec3,
                    clear_color=(100, 160, 220)) -> None:
        self.framebuffer.clear(clear_color)
        self.view = Mat4.look_at(eye, target, Vec3(0, 1, 0))

    def draw_triangle(self, a: Vec3, b: Vec3, c: Vec3, color) -> None:
        """Transform and rasterize a triangle whose vertices are in world space."""
        matrix = self.projection @ self.view
        clip = [matrix.transform4((v.x, v.y, v.z, 1.0)) for v in (a, b, c)]
        # Conservative reject until proper homogeneous clipping is implemented.
        # This avoids invalid perspective divides, but may discard triangles crossing
        # the near plane; a later renderer part will implement polygon clipping.
        if any(v[3] <= 1e-9 for v in clip):
            return
        ndc = [(v[0]/v[3], v[1]/v[3], v[2]/v[3]) for v in clip]
        if all((p[0] < -1 or p[0] > 1 or p[1] < -1 or p[1] > 1 or
                p[2] < -1 or p[2] > 1) for p in ndc):
            return
        screen = [((p[0]*0.5+0.5)*(self.width-1),
                   (1.0-(p[1]*0.5+0.5))*(self.height-1), p[2]) for p in ndc]
        self._rasterize(*screen, color)

    def _rasterize(self, a, b, c, color) -> None:
        ax, ay, az = a
        bx, by, bz = b
        cx, cy, cz = c
        area = (bx-ax)*(cy-ay) - (by-ay)*(cx-ax)
        if abs(area) < 1e-12:
            return
        min_x = max(0, math.floor(min(ax, bx, cx)))
        max_x = min(self.width-1, math.ceil(max(ax, bx, cx)))
        min_y = max(0, math.floor(min(ay, by, cy)))
        max_y = min(self.height-1, math.ceil(max(ay, by, cy)))
        for y in range(min_y, max_y+1):
            py = y + 0.5
            for x in range(min_x, max_x+1):
                px = x + 0.5
                w0 = ((bx-px)*(cy-py) - (by-py)*(cx-px)) / area
                w1 = ((cx-px)*(ay-py) - (cy-py)*(ax-px)) / area
                w2 = 1.0 - w0 - w1
                if w0 >= -1e-9 and w1 >= -1e-9 and w2 >= -1e-9:
                    z = w0*az + w1*bz + w2*cz
                    self.framebuffer.put_pixel(x, y, z, color)
