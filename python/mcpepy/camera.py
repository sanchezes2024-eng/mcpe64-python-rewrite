"""First-person camera math for the standalone Python voxel prototype."""
from __future__ import annotations
from dataclasses import dataclass
import math
from .math3d import Vec3

@dataclass
class Camera:
    position: Vec3
    yaw: float = 0.0
    pitch: float = -0.12
    fov_y: float = 70.0

    def __post_init__(self):
        self.pitch = max(-math.radians(89), min(math.radians(89), self.pitch))

    @property
    def forward(self) -> Vec3:
        cp=math.cos(self.pitch)
        return Vec3(math.sin(self.yaw)*cp, math.sin(self.pitch), -math.cos(self.yaw)*cp).normalized()

    @property
    def right(self) -> Vec3:
        return Vec3(math.cos(self.yaw), 0.0, math.sin(self.yaw)).normalized()

    @property
    def target(self) -> Vec3:
        return self.position + self.forward

    def rotate(self, yaw_delta: float, pitch_delta: float):
        self.yaw += float(yaw_delta)
        self.pitch = max(-math.radians(89), min(math.radians(89), self.pitch+float(pitch_delta)))

    def move_local(self, forward: float, strafe: float, vertical: float = 0.0):
        direction=self.forward*forward + self.right*strafe + Vec3(0,vertical,0)
        self.position=self.position+direction
