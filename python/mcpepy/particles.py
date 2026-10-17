"""Small deterministic particle simulation for the voxel prototype."""
from __future__ import annotations

from dataclasses import dataclass
import random


@dataclass
class Particle:
    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float
    color: tuple[float, float, float]
    age: float = 0.0
    lifetime: float = 0.45


class ParticleEngine:
    """Lightweight debris particles with gravity, drag, and bounded lifetime."""

    BLOCK_COLORS = {
        1: (0.34, 0.62, 0.22),  # grass
        2: (0.48, 0.31, 0.18),  # dirt
        3: (0.48, 0.48, 0.48),  # stone
        4: (0.22, 0.22, 0.22),  # bedrock
    }

    def __init__(self, seed: int = 0):
        self._random = random.Random(seed)
        self.particles: list[Particle] = []

    def emit_block_break(self, x: int, y: int, z: int, block_id: int, count: int = 10) -> None:
        color = self.BLOCK_COLORS.get(int(block_id), (0.8, 0.2, 0.8))
        for _ in range(max(0, int(count))):
            self.particles.append(Particle(
                x + self._random.uniform(0.15, 0.85),
                y + self._random.uniform(0.15, 0.85),
                z + self._random.uniform(0.15, 0.85),
                self._random.uniform(-2.2, 2.2),
                self._random.uniform(0.4, 3.0),
                self._random.uniform(-2.2, 2.2),
                color,
                lifetime=self._random.uniform(0.25, 0.65),
            ))

    def update(self, dt: float) -> None:
        dt = min(0.05, max(0.0, float(dt)))
        alive = []
        for p in self.particles:
            p.age += dt
            if p.age >= p.lifetime:
                continue
            p.vy -= 9.8 * dt
            drag = max(0.0, 1.0 - 2.2 * dt)
            p.vx *= drag
            p.vz *= drag
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.z += p.vz * dt
            alive.append(p)
        self.particles = alive

    def clear(self) -> None:
        self.particles.clear()
