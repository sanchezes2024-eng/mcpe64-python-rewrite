import unittest
from mcpepy.math3d import Vec3
from mcpepy.renderer import SoftwareRenderer
from mcpepy.texture import Texture
from mcpepy.voxel import STONE
from mcpepy.world import World
from mcpepy.chunkmesh import build_world_mesh, draw_world

class ChunkMeshTests(unittest.TestCase):
    def test_one_voxel_builds_six_quads(self):
        world=World(2,4,2)
        world.set_block(0,1,0,STONE)
        mesh=build_world_mesh(world)
        self.assertEqual(len(mesh.faces),6)
        self.assertEqual(mesh.triangle_count,12)
        self.assertEqual(mesh.vertex_count,24)

    def test_adjacent_voxels_hide_shared_faces(self):
        world=World(2,4,2)
        world.set_block(0,1,0,STONE)
        world.set_block(1,1,0,STONE)
        mesh=build_world_mesh(world)
        self.assertEqual(len(mesh.faces),10)
        self.assertFalse(any(f.direction=="east" and f.vertices[0].x==1 for f in mesh.faces))
        self.assertFalse(any(f.direction=="west" and f.vertices[0].x==1 for f in mesh.faces))

    def test_world_mesh_draws_with_texture(self):
        world=World(2,4,2)
        world.set_block(0,1,0,STONE)
        r=SoftwareRenderer(64,64)
        r.begin_frame(Vec3(2,2,4),Vec3(.5,1,.5),(0,0,0))
        count=draw_world(r,world,textures={STONE:Texture.solid((40,80,220))})
        self.assertEqual(count,12)
        self.assertIn(bytes((40,80,220)),r.framebuffer.color)

if __name__=="__main__":
    unittest.main()
