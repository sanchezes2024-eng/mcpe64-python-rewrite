"""Chunk manager and deterministic terrain generation for the clean-room Python engine.

This is an original prototype API, not a translation of native game source.
World coordinates may be negative; chunks are addressed with floor division.
"""
from __future__ import annotations

import math
from typing import Iterator

from .voxel import AIR, BLOCKS, GRASS, DIRT, STONE, Chunk, Face


class World:
    """A sparse collection of chunks with consistent world-coordinate access."""

    def __init__(self, chunk_width: int = 16, chunk_height: int = 128,
                 chunk_depth: int = 16):
        self.chunk_width = int(chunk_width)
        self.chunk_height = int(chunk_height)
        self.chunk_depth = int(chunk_depth)
        if min(self.chunk_width, self.chunk_height, self.chunk_depth) <= 0:
            raise ValueError("world chunk dimensions must be positive")
        self.chunks: dict[tuple[int, int], Chunk] = {}

    def get_chunk(self, chunk_x: int, chunk_z: int, create: bool = False) -> Chunk | None:
        key = (int(chunk_x), int(chunk_z))
        chunk = self.chunks.get(key)
        if chunk is None and create:
            chunk = Chunk(self.chunk_width, self.chunk_height, self.chunk_depth)
            self.chunks[key] = chunk
        return chunk

    def _locate(self, x: int, y: int, z: int) -> tuple[tuple[int, int], tuple[int, int, int]]:
        if not 0 <= y < self.chunk_height:
            raise IndexError(f"world Y coordinate out of range: {y}")
        cx, lx = divmod(int(x), self.chunk_width)
        cz, lz = divmod(int(z), self.chunk_depth)
        return (cx, cz), (lx, int(y), lz)

    def get_block(self, x: int, y: int, z: int) -> int:
        key, local = self._locate(x, y, z)
        chunk = self.chunks.get(key)
        return AIR if chunk is None else chunk.get(*local)

    def set_block(self, x: int, y: int, z: int, block_id: int) -> None:
        key, local = self._locate(x, y, z)
        self.get_chunk(*key, create=True).set(*local, block_id)

    def visible_faces(self) -> Iterator[Face]:
        """Yield faces visible across chunk boundaries as world-space coordinates."""
        for (cx, cz), chunk in sorted(self.chunks.items()):
            for x, y, z, block_id in chunk.iter_blocks():
                wx = cx * self.chunk_width + x
                wz = cz * self.chunk_depth + z
                for dx, dy, dz, direction in Chunk.DIRECTIONS:
                    ny = y + dy
                    # Outside the vertical world bounds is exposed air for meshing.
                    if not 0 <= ny < self.chunk_height:
                        yield Face(wx, y, wz, direction, block_id)
                        continue
                    adjacent_id = self.get_block(wx + dx, ny, wz + dz)
                    adjacent = BLOCKS.get(adjacent_id)
                    if adjacent_id == AIR or adjacent is None or adjacent.transparent:
                        yield Face(wx, y, wz, direction, block_id)


def _lattice(seed: int, x: int, z: int) -> float:
    """Stable pseudo-random value in [0, 1), independent of Python hash randomization."""
    n = (seed & 0xFFFFFFFF) ^ ((x * 0x1F123BB5) & 0xFFFFFFFF)
    n = (n ^ ((z * 0x5F356495) & 0xFFFFFFFF)) & 0xFFFFFFFF
    n = (n ^ (n >> 16)) * 0x7FEB352D & 0xFFFFFFFF
    n = (n ^ (n >> 15)) * 0x846CA68B & 0xFFFFFFFF
    n ^= n >> 16
    return (n & 0xFFFFFFFF) / 4294967296.0


def _smooth(t: float) -> float:
    return t * t * (3.0 - 2.0 * t)


def _value_noise(seed: int, x: float, z: float, scale: float) -> float:
    gx, gz = x / scale, z / scale
    x0, z0 = math.floor(gx), math.floor(gz)
    tx, tz = _smooth(gx - x0), _smooth(gz - z0)
    a = _lattice(seed, x0, z0)
    b = _lattice(seed, x0 + 1, z0)
    c = _lattice(seed, x0, z0 + 1)
    d = _lattice(seed, x0 + 1, z0 + 1)
    top = a + (b - a) * tx
    bottom = c + (d - c) * tx
    return top + (bottom - top) * tz


def generate_terrain_chunk(world: World, chunk_x: int, chunk_z: int,
                           seed: int = 0, base_height: int = 12,
                           amplitude: int = 5) -> Chunk:
    """Generate repeatable, gently rolling grass/dirt/stone terrain.

    This is a development terrain generator, not a claim of matching Minecraft's
    original terrain algorithm.
    """
    if base_height < 1 or base_height >= world.chunk_height:
        raise ValueError("base_height must be within the world height")
    if amplitude < 0:
        raise ValueError("amplitude cannot be negative")
    chunk = world.get_chunk(chunk_x, chunk_z, create=True)
    for lx in range(world.chunk_width):
        wx = chunk_x * world.chunk_width + lx
        for lz in range(world.chunk_depth):
            wz = chunk_z * world.chunk_depth + lz
            noise = (_value_noise(seed, wx, wz, 32.0) * 0.65
                     + _value_noise(seed ^ 0x5A17, wx, wz, 9.0) * 0.35)
            top = max(0, min(world.chunk_height - 1,
                             int(round(base_height + (noise - 0.5) * 2 * amplitude))))
            for y in range(top + 1):
                if y == top:
                    block = GRASS
                elif y >= top - 2:
                    block = DIRT
                else:
                    block = STONE
                chunk.set(lx, y, lz, block)
    return chunk
