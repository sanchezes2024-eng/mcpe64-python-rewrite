"""Basic axis-aligned collision helpers for the clean-room Python engine.

Coordinates are in block units. AABB minima are inclusive and maxima exclusive.
This is a deliberately small physics foundation, not a full player controller.
"""
from __future__ import annotations

from dataclasses import dataclass

from .voxel import AIR
from .world import World


@dataclass(frozen=True)
class AABB:
    min_x: float
    min_y: float
    min_z: float
    max_x: float
    max_y: float
    max_z: float

    def __post_init__(self) -> None:
        if self.min_x > self.max_x or self.min_y > self.max_y or self.min_z > self.max_z:
            raise ValueError("AABB minimums must not exceed maximums")

    def translated(self, dx: float, dy: float, dz: float) -> "AABB":
        return AABB(self.min_x + dx, self.min_y + dy, self.min_z + dz,
                    self.max_x + dx, self.max_y + dy, self.max_z + dz)


@dataclass(frozen=True)
class MoveResult:
    bounds: AABB
    collided_x: bool
    collided_y: bool
    collided_z: bool
    grounded: bool


def _block_is_solid(world: World, x: int, y: int, z: int) -> bool:
    # Treat below-world space as a solid floor; above-world space is empty.
    if y < 0:
        return True
    if y >= world.chunk_height:
        return False
    return world.get_block(x, y, z) != AIR


def collides(world: World, bounds: AABB) -> bool:
    """Return whether an AABB overlaps any solid voxel."""
    min_x, max_x = int(bounds.min_x // 1), int((bounds.max_x - 1e-9) // 1)
    min_y, max_y = int(bounds.min_y // 1), int((bounds.max_y - 1e-9) // 1)
    min_z, max_z = int(bounds.min_z // 1), int((bounds.max_z - 1e-9) // 1)
    for y in range(min_y, max_y + 1):
        for z in range(min_z, max_z + 1):
            for x in range(min_x, max_x + 1):
                if _block_is_solid(world, x, y, z):
                    return True
    return False


def move_and_collide(world: World, bounds: AABB,
                     dx: float, dy: float, dz: float) -> MoveResult:
    """Move on each axis independently, stopping at solid voxel boundaries."""
    collided_x = collided_y = collided_z = False
    grounded = False

    # X axis
    candidate = bounds.translated(dx, 0, 0)
    if not collides(world, candidate):
        bounds = candidate
    else:
        collided_x = True
        if dx > 0:
            max_x = bounds.max_x
            for y in range(int(bounds.min_y // 1), int((bounds.max_y - 1e-9) // 1) + 1):
                for z in range(int(bounds.min_z // 1), int((bounds.max_z - 1e-9) // 1) + 1):
                    bx = int((max_x + dx) // 1)
                    if _block_is_solid(world, bx, y, z):
                        dx = min(dx, bx - max_x)
            bounds = bounds.translated(max(0.0, dx), 0, 0)
        elif dx < 0:
            min_x = bounds.min_x
            for y in range(int(bounds.min_y // 1), int((bounds.max_y - 1e-9) // 1) + 1):
                for z in range(int(bounds.min_z // 1), int((bounds.max_z - 1e-9) // 1) + 1):
                    bx = int((min_x + dx) // 1)
                    if _block_is_solid(world, bx, y, z):
                        dx = max(dx, bx + 1 - min_x)
            bounds = bounds.translated(min(0.0, dx), 0, 0)

    # Y axis
    candidate = bounds.translated(0, dy, 0)
    if not collides(world, candidate):
        bounds = candidate
    else:
        collided_y = True
        if dy < 0:
            min_y = bounds.min_y
            target_y = min_y + dy
            block_y = int(target_y // 1)
            for x in range(int(bounds.min_x // 1), int((bounds.max_x - 1e-9) // 1) + 1):
                for z in range(int(bounds.min_z // 1), int((bounds.max_z - 1e-9) // 1) + 1):
                    if _block_is_solid(world, x, block_y, z):
                        dy = max(dy, block_y + 1 - min_y)
            grounded = True
            bounds = bounds.translated(0, min(0.0, dy), 0)
        elif dy > 0:
            max_y = bounds.max_y
            target_y = max_y + dy
            block_y = int((target_y - 1e-9) // 1)
            for x in range(int(bounds.min_x // 1), int((bounds.max_x - 1e-9) // 1) + 1):
                for z in range(int(bounds.min_z // 1), int((bounds.max_z - 1e-9) // 1) + 1):
                    if _block_is_solid(world, x, block_y, z):
                        dy = min(dy, block_y - max_y)
            bounds = bounds.translated(0, max(0.0, dy), 0)

    # Z axis
    candidate = bounds.translated(0, 0, dz)
    if not collides(world, candidate):
        bounds = candidate
    else:
        collided_z = True
        if dz > 0:
            max_z = bounds.max_z
            for x in range(int(bounds.min_x // 1), int((bounds.max_x - 1e-9) // 1) + 1):
                for y in range(int(bounds.min_y // 1), int((bounds.max_y - 1e-9) // 1) + 1):
                    bz = int((max_z + dz) // 1)
                    if _block_is_solid(world, x, y, bz):
                        dz = min(dz, bz - max_z)
            bounds = bounds.translated(0, 0, max(0.0, dz))
        elif dz < 0:
            min_z = bounds.min_z
            for x in range(int(bounds.min_x // 1), int((bounds.max_x - 1e-9) // 1) + 1):
                for y in range(int(bounds.min_y // 1), int((bounds.max_y - 1e-9) // 1) + 1):
                    bz = int((min_z + dz) // 1)
                    if _block_is_solid(world, x, y, bz):
                        dz = max(dz, bz + 1 - min_z)
            bounds = bounds.translated(0, 0, min(0.0, dz))

    return MoveResult(bounds, collided_x, collided_y, collided_z, grounded)
