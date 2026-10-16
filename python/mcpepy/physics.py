"""Voxel collision port following the original Entity::move axis-clipping order.

The native implementation gathers solid AABBs over the swept player box, clips
vertical motion first, then X and Z, and derives grounded/collision state from
the requested versus accepted movement. This module mirrors that core behavior
for full-cube blocks; tile-specific shapes and step-up behavior are separate.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import floor

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

    def expand(self, dx: float, dy: float, dz: float) -> "AABB":
        """Match native AABB::expand: extend only in the direction of motion."""
        return AABB(
            self.min_x + min(0.0, dx), self.min_y + min(0.0, dy),
            self.min_z + min(0.0, dz), self.max_x + max(0.0, dx),
            self.max_y + max(0.0, dy), self.max_z + max(0.0, dz),
        )


@dataclass(frozen=True)
class MoveResult:
    bounds: AABB
    collided_x: bool
    collided_y: bool
    collided_z: bool
    grounded: bool


def _block_is_solid(world: World, x: int, y: int, z: int) -> bool:
    # Entity movement in the native game collides with the bottom of the world.
    if y < 0:
        return True
    if y >= world.chunk_height:
        return False
    return world.get_block(x, y, z) != AIR


def _intersects(a: AABB, b: AABB) -> bool:
    # Same strict-edge behavior as native AABB::intersects.
    return not (
        a.max_x <= b.min_x or a.min_x >= b.max_x
        or a.max_y <= b.min_y or a.min_y >= b.max_y
        or a.max_z <= b.min_z or a.min_z >= b.max_z
    )


def _solid_boxes(world: World, bounds: AABB) -> list[AABB]:
    """Collect full-cube collision boxes within a swept bounding box."""
    # The tiny epsilon excludes a block that only touches a maximum face.
    x0, x1 = floor(bounds.min_x), floor(bounds.max_x - 1e-9)
    y0, y1 = floor(bounds.min_y), floor(bounds.max_y - 1e-9)
    z0, z1 = floor(bounds.min_z), floor(bounds.max_z - 1e-9)
    result = []
    for y in range(y0, y1 + 1):
        for z in range(z0, z1 + 1):
            for x in range(x0, x1 + 1):
                if _block_is_solid(world, x, y, z):
                    result.append(AABB(x, y, z, x + 1, y + 1, z + 1))
    return result


def collides(world: World, bounds: AABB) -> bool:
    """Return whether an AABB overlaps any solid voxel."""
    return any(_intersects(bounds, block) for block in _solid_boxes(world, bounds))


def _clip_y(block: AABB, box: AABB, dy: float) -> float:
    if box.max_x <= block.min_x or box.min_x >= block.max_x:
        return dy
    if box.max_z <= block.min_z or box.min_z >= block.max_z:
        return dy
    if dy > 0 and box.max_y <= block.min_y:
        dy = min(dy, block.min_y - box.max_y)
    elif dy < 0 and box.min_y >= block.max_y:
        dy = max(dy, block.max_y - box.min_y)
    return dy


def _clip_x(block: AABB, box: AABB, dx: float) -> float:
    if box.max_y <= block.min_y or box.min_y >= block.max_y:
        return dx
    if box.max_z <= block.min_z or box.min_z >= block.max_z:
        return dx
    if dx > 0 and box.max_x <= block.min_x:
        dx = min(dx, block.min_x - box.max_x)
    elif dx < 0 and box.min_x >= block.max_x:
        dx = max(dx, block.max_x - box.min_x)
    return dx


def _clip_z(block: AABB, box: AABB, dz: float) -> float:
    if box.max_x <= block.min_x or box.min_x >= block.max_x:
        return dz
    if box.max_y <= block.min_y or box.min_y >= block.max_y:
        return dz
    if dz > 0 and box.max_z <= block.min_z:
        dz = min(dz, block.min_z - box.max_z)
    elif dz < 0 and box.min_z >= block.max_z:
        dz = max(dz, block.max_z - box.min_z)
    return dz


def move_and_collide(world: World, bounds: AABB,
                     dx: float, dy: float, dz: float) -> MoveResult:
    """Resolve motion like native Entity::move: Y first, then X, then Z."""
    requested_x, requested_y, requested_z = dx, dy, dz
    obstacles = _solid_boxes(world, bounds.expand(dx, dy, dz))

    # The original engine resolves vertical motion before horizontal movement.
    for block in obstacles:
        dy = _clip_y(block, bounds, dy)
    bounds = bounds.translated(0.0, dy, 0.0)

    for block in obstacles:
        dx = _clip_x(block, bounds, dx)
    bounds = bounds.translated(dx, 0.0, 0.0)

    for block in obstacles:
        dz = _clip_z(block, bounds, dz)
    bounds = bounds.translated(0.0, 0.0, dz)

    collided_x = abs(dx - requested_x) > 1e-9
    collided_y = abs(dy - requested_y) > 1e-9
    collided_z = abs(dz - requested_z) > 1e-9
    grounded = collided_y and requested_y < 0.0
    return MoveResult(bounds, collided_x, collided_y, collided_z, grounded)
