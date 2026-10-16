"""Small playable simulation loop joining camera, world, renderer and collision."""
from __future__ import annotations
from dataclasses import dataclass, field
from .camera import Camera
from .chunkmesh import draw_world
from .math3d import Vec3
from .physics import AABB, move_and_collide
from .renderer import SoftwareRenderer
from .voxel import STONE
from .world import World, generate_terrain_chunk

@dataclass
class Game:
    width: int = 240
    height: int = 180
    seed: int = 7
    world: World = field(init=False)
    renderer: SoftwareRenderer = field(init=False)
    camera: Camera = field(init=False)
    player_x: float = field(init=False, default=8.0)
    player_y: float = field(init=False, default=5.0)
    player_z: float = field(init=False, default=8.0)
    vertical_speed: float = field(init=False, default=0.0)
    grounded: bool = field(init=False, default=False)
    yaw: float = field(init=False, default=0.0)
    pitch: float = field(init=False, default=-0.38)
    last_triangles: int = field(init=False, default=0)

    def __post_init__(self):
        self.world=World(16,32,16)
        generate_terrain_chunk(self.world,0,0,seed=self.seed,base_height=3,amplitude=1)
        self.renderer=SoftwareRenderer(self.width,self.height,near=.08,far=64)
        self._sync_camera()

    def _sync_camera(self):
        self.camera=Camera(Vec3(self.player_x,self.player_y+1.55,self.player_z),self.yaw,self.pitch)

    def player_bounds(self):
        radius=.28
        return AABB(self.player_x-radius,self.player_y,self.player_z-radius,
                    self.player_x+radius,self.player_y+1.8,self.player_z+radius)

    def jump(self):
        if self.grounded:
            self.vertical_speed=8.0
            self.grounded=False

    def step(self, keys=(), dt=1/30, look_x=0.0, look_y=0.0):
        """Advance a simulation frame. Keys are lowercase names like 'w','space'."""
        dt=max(0.0,float(dt))
        keys=set(keys)
        self.yaw += float(look_x)*dt
        self.pitch=max(-1.5533,min(1.5533,self.pitch+float(look_y)*dt))
        forward_x,forward_z=__import__("math").sin(self.yaw),-__import__("math").cos(self.yaw)
        right_x,right_z=__import__("math").cos(self.yaw),__import__("math").sin(self.yaw)
        mx=mz=0.0
        if "w" in keys: mx+=forward_x; mz+=forward_z
        if "s" in keys: mx-=forward_x; mz-=forward_z
        if "d" in keys: mx+=right_x; mz+=right_z
        if "a" in keys: mx-=right_x; mz-=right_z
        length=(mx*mx+mz*mz)**.5
        if length>0:
            mx,mz=mx/length,mz/length
        # Native KeyboardInput scales movement input to 0.3 while sneaking.
        speed=4.3*(0.3 if "shift" in keys else 1.0)
        self.vertical_speed-=32.0*dt
        result=move_and_collide(self.world,self.player_bounds(),mx*speed*dt,
                                self.vertical_speed*dt,mz*speed*dt)
        self.player_x=(result.bounds.min_x+result.bounds.max_x)*.5
        self.player_y=result.bounds.min_y
        self.player_z=(result.bounds.min_z+result.bounds.max_z)*.5
        self.grounded=result.grounded
        if result.collided_y:
            self.vertical_speed=0.0
        if "space" in keys:
            self.jump()
        self._sync_camera()

    def render(self):
        self.renderer.begin_frame(self.camera.position,self.camera.target,(116,174,224))
        self.last_triangles=draw_world(self.renderer,self.world,fog=True)
        return self.renderer.framebuffer.to_ppm()
