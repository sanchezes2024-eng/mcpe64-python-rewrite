"""Independent voxel data model for the Python reimplementation.

This module intentionally defines a small new API rather than translating game
source. Chunks store one-byte block IDs in Y-major layers and expose visible
block faces for a renderer to consume.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Optional


AIR = 0
GRASS = 1
DIRT = 2
STONE = 3
BEDROCK = 4


@dataclass(frozen=True)
class Block:
    block_id: int
    name: str
    solid: bool = True


BLOCKS = {
    AIR: Block(AIR, "air", False),
    GRASS: Block(GRASS, "grass"),
    DIRT: Block(DIRT, "dirt"),
    STONE: Block(STONE, "stone"),
    BEDROCK: Block(BEDROCK, "bedrock"),
}


@dataclass(frozen=True)
class Face:
    """A visible axis-aligned face in chunk-local coordinates."""
    x: int
    y: int
    z: int
    direction: str
    block_id: int


class Chunk:
    """Compact fixed-size voxel chunk; coordinates are local to this chunk."""

    DIRECTIONS = (
        (0, 1, 0, "top"),
        (0, -1, 0, "bottom"),
        (1, 0, 0, "east"),
        (-1, 0, 0, "west"),
        (0, 0, 1, "south"),
        (0, 0, -1, "north"),
    )

    def __init__(self, width: int = 16, height: int = 64, depth: int = 16):
        if min(width, height, depth) <= 0:
            raise ValueError("chunk dimensions must be positive")
        if len(BLOCKS) > 256:
            raise ValueError("block IDs must fit in one byte")
        self.width, self.height, self.depth = int(width), int(height), int(depth)
        self.blocks = bytearray(self.width * self.height * self.depth)

    def _index(self, x: int, y: int, z: int) -> int:
        if not (0 <= x < self.width and 0 <= y < self.height and 0 <= z < self.depth):
            raise IndexError(f"block coordinate out of range: {(x, y, z)}")
        return (y * self.depth + z) * self.width + x

    def get(self, x: int, y: int, z: int) -> int:
        return self.blocks[self._index(x, y, z)]

    def set(self, x: int, y: int, z: int, block_id: int) -> None:
        if not 0 <= int(block_id) <= 255:
            raise ValueError("block ID must be in range 0..255")
        self.blocks[self._index(x, y, z)] = int(block_id)

    def fill(self, block_id: int) -> None:
        if not 0 <= int(block_id) <= 255:
            raise ValueError("block ID must be in range 0..255")
        self.blocks[:] = bytes((int(block_id),)) * len(self.blocks)

    def iter_blocks(self) -> Iterator[tuple[int, int, int, int]]:
        """Yield non-air blocks as (x, y, z, block_id)."""
        for y in range(self.height):
            for z in range(self.depth):
                row = (y * self.depth + z) * self.width
                for x in range(self.width):
                    block_id = self.blocks[row + x]
                    if block_id != AIR:
                        yield x, y, z, block_id

    def visible_faces(self, neighbor: Optional["Chunk"] = None) -> Iterator[Face]:
        """Yield faces adjacent to air.

        Faces on chunk boundaries are visible unless a neighboring chunk is
        supplied. Boundary-neighbor stitching is intentionally left for the
        world/chunk-manager layer, where neighboring chunk coordinates are known.
        """
        for x, y, z, block_id in self.iter_blocks():
            for dx, dy, dz, direction in self.DIRECTIONS:
                nx, ny, nz = x + dx, y + dy, z + dz
                if 0 <= nx < self.width and 0 <= ny < self.height and 0 <= nz < self.depth:
                    adjacent = self.get(nx, ny, nz)
                    if adjacent != AIR and BLOCKS.get(adjacent, Block(adjacent, "unknown")).solid:
                        continue
                yield Face(x, y, z, direction, block_id)

    def count_non_air(self) -> int:
        return sum(1 for value in self.blocks if value != AIR)


def generate_flat_chunk(
    width: int = 16, height: int = 64, depth: int = 16,
    ground_y: int = 8,
) -> Chunk:
    """Generate a deterministic grass/dirt/stone test terrain."""
    if not 0 <= ground_y < height:
        raise ValueError("ground_y must be inside the chunk")
    chunk = Chunk(width, height, depth)
    for x in range(width):
        for z in range(depth):
            chunk.set(x, ground_y, z, GRASS)
            if ground_y > 0:
                chunk.set(x, ground_y - 1, z, DIRT)
            for y in range(0, max(0, ground_y - 1)):
                chunk.set(x, y, z, STONE)
    return chunk
