"""Dependency-free RGB framebuffer with depth testing and alpha blending."""
from __future__ import annotations
from typing import Iterable, Tuple

class Framebuffer:
    def __init__(self,width:int,height:int,clear_color=(100,160,220)):
        if width<1 or height<1:
            raise ValueError("framebuffer dimensions must be positive")
        self.width,self.height=int(width),int(height)
        self.color=bytearray(self.width*self.height*3)
        self.depth=[float("inf")]*(self.width*self.height)
        self.clear(clear_color)

    def clear(self,color=(100,160,220)):
        r,g,b=self._rgb(color)
        self.color[:]=bytes((r,g,b))*(self.width*self.height)
        self.depth[:]=[float("inf")]*(self.width*self.height)

    @staticmethod
    def _rgb(color:Iterable[int])->Tuple[int,int,int]:
        values=tuple(color)
        if len(values)!=3:
            raise ValueError("color must have three channels")
        return tuple(max(0,min(255,int(c))) for c in values)

    def put_pixel(self,x:int,y:int,depth:float,color,*,alpha=255)->bool:
        if x<0 or y<0 or x>=self.width or y>=self.height:
            return False
        alpha=max(0,min(255,int(alpha)))
        if alpha==0:
            return False
        index=y*self.width+x
        if depth>=self.depth[index]:
            return False
        self.depth[index]=depth; off=index*3; rgb=self._rgb(color)
        if alpha==255:
            self.color[off:off+3]=bytes(rgb)
        else:
            inv=255-alpha
            self.color[off:off+3]=bytes((rgb[i]*alpha+self.color[off+i]*inv+127)//255 for i in range(3))
        return True

    def to_ppm(self):
        header=f"P6\n{self.width} {self.height}\n255\n".encode("ascii")
        return header+bytes(self.color)
