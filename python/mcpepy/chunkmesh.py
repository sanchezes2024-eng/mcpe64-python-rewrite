"""Visible-face mesh generation and bridge from voxel worlds to SoftwareRenderer."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
from .math3d import Vec3
from .voxel import BLOCKS, Face
from .world import World

QUAD_UVS=((0.0,0.0),(1.0,0.0),(1.0,1.0),(0.0,1.0))

@dataclass(frozen=True)
class MeshFace:
    block_id: int
    direction: str
    vertices: tuple[Vec3,Vec3,Vec3,Vec3]
    uvs: tuple[tuple[float,float],tuple[float,float],tuple[float,float],tuple[float,float]]

@dataclass(frozen=True)
class ChunkMesh:
    faces: tuple[MeshFace,...]

    @property
    def triangle_count(self):
        return len(self.faces)*2

    @property
    def vertex_count(self):
        return len(self.faces)*4


def _face_vertices(face: Face):
    x,y,z=float(face.x),float(face.y),float(face.z)
    # Consistent quad layout; the renderer currently does not cull by winding.
    corners={
        "top": ((x,y+1,z),(x+1,y+1,z),(x+1,y+1,z+1),(x,y+1,z+1)),
        "bottom": ((x,y,z+1),(x+1,y,z+1),(x+1,y,z),(x,y,z)),
        "east": ((x+1,y,z),(x+1,y,z+1),(x+1,y+1,z+1),(x+1,y+1,z)),
        "west": ((x,y,z+1),(x,y,z),(x,y+1,z),(x,y+1,z+1)),
        "south": ((x+1,y,z+1),(x,y,z+1),(x,y+1,z+1),(x+1,y+1,z+1)),
        "north": ((x,y,z),(x+1,y,z),(x+1,y+1,z),(x,y+1,z)),
    }
    try:
        raw=corners[face.direction]
    except KeyError as exc:
        raise ValueError("unknown voxel face direction: "+str(face.direction)) from exc
    return tuple(Vec3(*p) for p in raw)


def build_world_mesh(world: World) -> ChunkMesh:
    """Build quads only for faces exposed to air, including chunk boundaries."""
    return ChunkMesh(tuple(
        MeshFace(face.block_id,face.direction,_face_vertices(face),QUAD_UVS)
        for face in world.visible_faces()
    ))


def draw_world(renderer, world: World, *, textures: Mapping[int,object] | None=None,
               colors: Mapping[int,tuple[int,int,int]] | None=None,
               face_light: Mapping[str,float] | None=None, fog=False) -> int:
    """Draw the current exposed voxel faces and return the number of triangles.

    Texture values must implement Texture.sample(u, v). Without a texture, a
    stable block colour is used. This simple per-face path favors clarity over
    batching; it is suitable for prototypes, not large-world performance.
    """
    textures=textures or {}
    colors=colors or {}
    face_light=face_light or {"top":1.0,"bottom":0.55,"east":0.8,
                              "west":0.8,"south":0.7,"north":0.7}
    palette={block_id: (120, 120, 120) for block_id in BLOCKS}
    palette.update({1:(120,120,120), 2:(90,180,70), 3:(130,90,55), 7:(65,65,65)})
    triangles=0
    for face in build_world_mesh(world).faces:
        v=face.vertices
        texture=textures.get(face.block_id)
        light=max(0.0,float(face_light.get(face.direction,1.0)))
        if texture is None:
            base=colors.get(face.block_id,palette.get(face.block_id,(180,0,180)))
            color=tuple(max(0,min(255,int(c*light))) for c in base)
            renderer.draw_triangle(v[0],v[1],v[2],color)
            renderer.draw_triangle(v[0],v[2],v[3],color)
        else:
            renderer.draw_textured_triangle(v[0],v[1],v[2],
                (face.uvs[0],face.uvs[1],face.uvs[2]),texture,light=light,fog=fog)
            renderer.draw_textured_triangle(v[0],v[2],v[3],
                (face.uvs[0],face.uvs[2],face.uvs[3]),texture,light=light,fog=fog)
        triangles+=2
    return triangles
