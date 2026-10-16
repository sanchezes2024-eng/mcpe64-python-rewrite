"""CPU triangle renderer with homogeneous clipping and textured triangles."""
from __future__ import annotations
import math
from .math3d import Mat4, Vec3
from .framebuffer import Framebuffer

class SoftwareRenderer:
    def __init__(self, width=640, height=400, fov_y=70.0, near=0.05, far=128.0):
        if width < 1 or height < 1:
            raise ValueError("render dimensions must be positive")
        self.width, self.height = int(width), int(height)
        self.fov_y, self.near, self.far = float(fov_y), float(near), float(far)
        self.framebuffer = Framebuffer(self.width, self.height)
        self.projection = Mat4.perspective(fov_y, self.width / self.height, near, far)
        self.view = Mat4.identity()
        self.fog_color = (100, 160, 220)

    def resize(self, width, height):
        if width < 1 or height < 1:
            raise ValueError("render dimensions must be positive")
        self.width, self.height = int(width), int(height)
        self.framebuffer = Framebuffer(self.width, self.height)
        self.projection = Mat4.perspective(self.fov_y, self.width / self.height, self.near, self.far)

    def begin_frame(self, eye: Vec3, target: Vec3, clear_color=(100, 160, 220)):
        self.framebuffer.clear(clear_color)
        self.view = Mat4.look_at(eye, target, Vec3(0, 1, 0))
        self.fog_color = tuple(clear_color)

    def draw_triangle(self, a: Vec3, b: Vec3, c: Vec3, color):
        """Draw a flat-colour world-space triangle, clipping against the view frustum."""
        matrix = self.projection @ self.view
        vertices = [matrix.transform4((v.x, v.y, v.z, 1.0)) + (0.0, 0.0) for v in (a,b,c)]
        self._draw_polygon(vertices, None, color, (255,255,255), 1.0, False)

    def draw_textured_triangle(self, a: Vec3, b: Vec3, c: Vec3, uvs, texture,
                               tint=(255,255,255), *, light=1.0, fog=False):
        """Draw a triangle with perspective-correct normalized UV interpolation."""
        if len(uvs) != 3:
            raise ValueError("exactly three UV coordinates are required")
        matrix = self.projection @ self.view
        vertices = []
        for point, uv in zip((a,b,c), uvs):
            if len(uv) != 2:
                raise ValueError("each UV coordinate must contain u and v")
            vertices.append(matrix.transform4((point.x,point.y,point.z,1.0)) + (float(uv[0]),float(uv[1])))
        self._draw_polygon(vertices, texture, (255,255,255), tint, max(0.0,float(light)), bool(fog))

    @staticmethod
    def _plane_distance(v, plane):
        x,y,z,w = v[:4]
        return (x+w,w-x,y+w,w-y,z+w,w-z)[plane]

    @classmethod
    def _clip_polygon(cls, polygon):
        # Sutherland-Hodgman clipping against all six homogeneous clip planes.
        for plane in range(6):
            if not polygon:
                break
            output = []
            previous = polygon[-1]
            d_prev = cls._plane_distance(previous, plane)
            for current in polygon:
                d_cur = cls._plane_distance(current, plane)
                inside_prev, inside_cur = d_prev >= 0, d_cur >= 0
                if inside_prev != inside_cur:
                    denom = d_prev - d_cur
                    t = 0.0 if abs(denom) < 1e-15 else d_prev / denom
                    output.append(tuple(a + (b-a)*t for a,b in zip(previous,current)))
                if inside_cur:
                    output.append(current)
                previous, d_prev = current, d_cur
            polygon = output
        return polygon

    def _draw_polygon(self, vertices, texture, color, tint, light, use_fog):
        polygon = self._clip_polygon(vertices)
        for i in range(1, len(polygon)-1):
            self._rasterize_vertex_triangle(polygon[0],polygon[i],polygon[i+1],
                                            texture,color,tint,light,use_fog)

    def _rasterize_vertex_triangle(self, va,vb,vc,texture,color,tint,light,use_fog):
        def screen(v):
            x,y,z,w,u,vv = v
            if w <= 1e-15:
                return None
            iw = 1.0/w
            return ((x*iw*0.5+0.5)*(self.width-1),
                    (1.0-(y*iw*0.5+0.5))*(self.height-1),
                    z*iw,iw,u,vv)
        a,b,c = screen(va),screen(vb),screen(vc)
        if a is None or b is None or c is None:
            return
        ax,ay=a[:2]; bx,by=b[:2]; cx,cy=c[:2]
        area=(bx-ax)*(cy-ay)-(by-ay)*(cx-ax)
        if abs(area)<1e-12:
            return
        min_x=max(0,math.floor(min(ax,bx,cx))); max_x=min(self.width-1,math.ceil(max(ax,bx,cx)))
        min_y=max(0,math.floor(min(ay,by,cy))); max_y=min(self.height-1,math.ceil(max(ay,by,cy)))
        for y in range(min_y,max_y+1):
            py=y+0.5
            for x in range(min_x,max_x+1):
                px=x+0.5
                w0=((bx-px)*(cy-py)-(by-py)*(cx-px))/area
                w1=((cx-px)*(ay-py)-(cy-py)*(ax-px))/area
                w2=1.0-w0-w1
                if w0 < -1e-9 or w1 < -1e-9 or w2 < -1e-9:
                    continue
                depth=w0*a[2]+w1*b[2]+w2*c[2]
                if texture is None:
                    rgba=(*Framebuffer._rgb(color),255)
                else:
                    denom=w0*a[3]+w1*b[3]+w2*c[3]
                    if denom<=1e-15:
                        continue
                    u=(w0*a[4]*a[3]+w1*b[4]*b[3]+w2*c[4]*c[3])/denom
                    v=(w0*a[5]*a[3]+w1*b[5]*b[3]+w2*c[5]*c[3])/denom
                    rgba=texture.sample(u,v)
                r,g,bl,alpha=rgba
                r=max(0,min(255,int(r*tint[0]/255.0*light)))
                g=max(0,min(255,int(g*tint[1]/255.0*light)))
                bl=max(0,min(255,int(bl*tint[2]/255.0*light)))
                if use_fog:
                    fog_t=min(1.0,max(0.0,((depth+1.0)*0.5-0.65)/0.35))
                    fr,fg,fb=self.fog_color
                    r=int(r*(1-fog_t)+fr*fog_t)
                    g=int(g*(1-fog_t)+fg*fog_t)
                    bl=int(bl*(1-fog_t)+fb*fog_t)
                self.framebuffer.put_pixel(x,y,depth,(r,g,bl),alpha=alpha)
