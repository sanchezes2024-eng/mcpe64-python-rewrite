"""Dependency-free RGB/RGBA texture with PPM and uncompressed BMP loaders."""
from __future__ import annotations
from dataclasses import dataclass
import struct
from pathlib import Path

@dataclass(frozen=True)
class Texture:
    width: int
    height: int
    pixels: bytes
    channels: int = 4

    def __post_init__(self):
        if self.width < 1 or self.height < 1:
            raise ValueError("texture dimensions must be positive")
        if self.channels not in (3,4):
            raise ValueError("channels must be 3 (RGB) or 4 (RGBA)")
        if len(self.pixels) != self.width*self.height*self.channels:
            raise ValueError("pixel byte count does not match dimensions")

    @classmethod
    def solid(cls, color=(255,255,255), width=1, height=1):
        if len(color) not in (3,4):
            raise ValueError("color must be RGB or RGBA")
        channels=len(color)
        pixel=bytes(max(0,min(255,int(c))) for c in color)
        return cls(width,height,pixel*(width*height),channels)

    def _rgba(self,x,y):
        off=(y*self.width+x)*self.channels
        values=tuple(self.pixels[off:off+self.channels])
        return values+((255,) if self.channels==3 else ())

    def sample(self,u,v,*,bilinear=False):
        """Sample normalized UV coordinates, clamping at the texture edges."""
        u=min(1.0,max(0.0,float(u))); v=min(1.0,max(0.0,float(v)))
        if not bilinear or self.width==1 or self.height==1:
            return self._rgba(min(self.width-1,int(u*self.width)),min(self.height-1,int(v*self.height)))
        fx=u*(self.width-1); fy=v*(self.height-1)
        x0=int(fx); y0=int(fy); x1=min(self.width-1,x0+1); y1=min(self.height-1,y0+1)
        tx=fx-x0; ty=fy-y0
        s=[self._rgba(x0,y0),self._rgba(x1,y0),self._rgba(x0,y1),self._rgba(x1,y1)]
        return tuple(int(round(s[0][i]*(1-tx)*(1-ty)+s[1][i]*tx*(1-ty)+s[2][i]*(1-tx)*ty+s[3][i]*tx*ty)) for i in range(4))

    @classmethod
    def load(cls,filename):
        data=Path(filename).read_bytes()
        if data.startswith((b"P6",b"P3")):
            return cls._load_ppm(data)
        if data.startswith(b"BM"):
            return cls._load_bmp(data)
        raise ValueError("unsupported texture format; use PPM or uncompressed BMP")

    @classmethod
    def _load_ppm(cls,data):
        pos=0; tokens=[]
        while len(tokens)<4:
            while pos<len(data) and data[pos] in b" \t\r\n":
                pos+=1
            if pos<len(data) and data[pos]==35:
                while pos<len(data) and data[pos] not in b"\r\n":
                    pos+=1
                continue
            start=pos
            while pos<len(data) and data[pos] not in b" \t\r\n#":
                pos+=1
            if start==pos:
                raise ValueError("invalid PPM header")
            tokens.append(data[start:pos])
        magic,w,h,maxval=tokens
        width,height,maximum=int(w),int(h),int(maxval)
        if width<1 or height<1 or not 1<=maximum<=255:
            raise ValueError("invalid PPM dimensions or maximum channel value")
        if magic==b"P6":
            if data[pos:pos+2]==b"\r\n": pos+=2
            elif pos<len(data) and data[pos] in b" \t\r\n": pos+=1
            raw=data[pos:]
            if len(raw)!=width*height*3:
                raise ValueError("PPM pixel payload has incorrect length")
            if maximum!=255: raw=bytes(round(c*255/maximum) for c in raw)
            return cls(width,height,raw,3)
        tail=data[pos:].decode("ascii")
        vals=[]
        for line in tail.splitlines():
            vals.extend(part for part in line.split("#",1)[0].split() if part)
        nums=[int(v) for v in vals]
        if len(nums)!=width*height*3:
            raise ValueError("PPM pixel payload has incorrect length")
        return cls(width,height,bytes(max(0,min(255,round(n*255/maximum))) for n in nums),3)

    @classmethod
    def _load_bmp(cls,data):
        if len(data)<54:
            raise ValueError("truncated BMP file")
        offset=struct.unpack_from("<I",data,10)[0]
        hs=struct.unpack_from("<I",data,14)[0]
        if hs<40 or len(data)<14+hs:
            raise ValueError("unsupported BMP header")
        width,signed_h,planes,bits,compression=struct.unpack_from("<iiHHI",data,18)
        if width<1 or signed_h==0 or planes!=1 or bits not in (24,32) or compression!=0:
            raise ValueError("only uncompressed 24/32-bit BMP textures are supported")
        height=abs(signed_h); stride=((width*(bits//8)+3)//4)*4
        if offset+stride*height>len(data):
            raise ValueError("truncated BMP pixel data")
        channels=4 if bits==32 else 3; pixels=bytearray(width*height*channels)
        for y in range(height):
            src_y=y if signed_h<0 else height-1-y
            for x in range(width):
                src=offset+src_y*stride+x*(bits//8); dst=(y*width+x)*channels
                b,g,r=data[src:src+3]; pixels[dst:dst+3]=bytes((r,g,b))
                if channels==4: pixels[dst+3]=data[src+3]
        return cls(width,height,bytes(pixels),channels)
