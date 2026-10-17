"""MCPE 0.6.1 block IDs and base tile properties, transcribed from Tile.cpp.

This is the source-grounded tile registry used by world storage and renderers.
It does not claim to port each C++ tile subclass's geometry, ticking, redstone,
or interaction behavior; those remain separate ports.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Optional

AIR = 0
GRASS = 2
DIRT = 3
STONE = 1
BEDROCK = 7

@dataclass(frozen=True)
class Block:
    block_id: int
    name: str
    solid: bool = True
    texture: int = 0
    shape: str = "cube"
    transparent: bool = False
    hardness: float = 1.5
    explosion_resistance: float = 10.0
    light_emission: int = 0
    material: str = "stone"

# id: (description id, base texture index, material, shape, transparent,
#      solid, destroy time, light emission). Texture numbers are the integer
# indices used by the original Tile subclasses in Tile.cpp.
_TILE_ROWS = {
    1: ("stone", 1, "stone", "cube", False, True, 1.5, 0),
    2: ("grass", 0, "earth", "cube", False, True, 0.6, 0),
    3: ("dirt", 2, "earth", "cube", False, True, 0.5, 0),
    4: ("stonebrick", 16, "stone", "cube", False, True, 2.0, 0),
    5: ("wood", 4, "wood", "cube", False, True, 2.0, 0),
    6: ("sapling", 15, "plant", "cross", True, False, 0.0, 0),
    7: ("bedrock", 17, "stone", "cube", False, True, -1.0, 0),
    8: ("water", 14, "water", "liquid", True, False, 100.0, 0),
    9: ("water", 14, "water", "liquid", True, False, 100.0, 0),
    10: ("lava", 30, "lava", "liquid", True, False, 0.0, 15),
    11: ("lava", 30, "lava", "liquid", True, False, 100.0, 15),
    12: ("sand", 18, "sand", "cube", False, True, 0.5, 0),
    13: ("gravel", 19, "sand", "cube", False, True, 0.6, 0),
    14: ("oreGold", 32, "stone", "cube", False, True, 3.0, 0),
    15: ("oreIron", 33, "stone", "cube", False, True, 3.0, 0),
    16: ("oreCoal", 34, "stone", "cube", False, True, 3.0, 0),
    17: ("log", 20, "wood", "cube", False, True, 2.0, 0),
    18: ("leaves", 52, "plant", "cube", True, True, 0.2, 0),
    20: ("glass", 49, "glass", "cube", True, True, 0.3, 0),
    21: ("oreLapis", 160, "stone", "cube", False, True, 3.0, 0),
    22: ("blockLapis", 144, "stone", "cube", False, True, 3.0, 0),
    24: ("sandStone", 192, "stone", "cube", False, True, 0.8, 0),
    26: ("bed", 0, "wood", "bed", True, False, 0.2, 0),
    30: ("web", 11, "plant", "cross", True, False, 4.0, 0),
    31: ("tallgrass", 39, "plant", "cross", True, False, 0.0, 0),
    35: ("cloth", 64, "cloth", "cube", False, True, 0.8, 0),
    37: ("flower", 13, "plant", "cross", True, False, 0.0, 0),
    38: ("rose", 12, "plant", "cross", True, False, 0.0, 0),
    39: ("mushroom", 29, "plant", "cross", True, False, 0.0, 2),
    40: ("mushroom", 28, "plant", "cross", True, False, 0.0, 0),
    41: ("blockGold", 23, "metal", "cube", False, True, 3.0, 0),
    42: ("blockIron", 22, "metal", "cube", False, True, 5.0, 0),
    43: ("stoneSlab", 1, "stone", "slab", False, True, 2.0, 0),
    44: ("stoneSlab", 1, "stone", "slab", False, True, 2.0, 0),
    45: ("brick", 7, "stone", "cube", False, True, 2.0, 0),
    46: ("tnt", 8, "earth", "cube", False, True, 0.0, 0),
    47: ("bookshelf", 35, "wood", "cube", False, True, 1.5, 0),
    48: ("stoneMoss", 36, "stone", "cube", False, True, 2.0, 0),
    49: ("obsidian", 37, "stone", "cube", False, True, 10.0, 0),
    50: ("torch", 80, "wood", "torch", True, False, 0.0, 15),
    51: ("fire", 31, "fire", "cross", True, False, 0.0, 15),
    53: ("stairsWood", 4, "wood", "stairs", False, True, 2.0, 0),
    54: ("chest", 25, "wood", "cube", False, True, 2.5, 0),
    56: ("oreDiamond", 50, "stone", "cube", False, True, 3.0, 0),
    57: ("blockDiamond", 24, "metal", "cube", False, True, 5.0, 0),
    58: ("workbench", 43, "wood", "cube", False, True, 2.5, 0),
    59: ("crops", 88, "plant", "cross", True, False, 0.0, 0),
    60: ("farmland", 87, "earth", "cube", False, True, 0.6, 0),
    61: ("furnace", 45, "stone", "cube", False, True, 3.5, 0),
    62: ("furnace", 45, "stone", "cube", False, True, 3.5, 14),
    63: ("sign", 4, "wood", "sign", True, False, 1.0, 0),
    64: ("doorWood", 97, "wood", "door", True, False, 3.0, 0),
    65: ("ladder", 83, "wood", "ladder", True, False, 0.4, 0),
    67: ("stairsStone", 16, "stone", "stairs", False, True, 2.0, 0),
    68: ("sign", 4, "wood", "sign", True, False, 1.0, 0),
    71: ("doorIron", 98, "metal", "door", True, False, 5.0, 0),
    73: ("oreRedstone", 51, "stone", "cube", False, True, 3.0, 0),
    74: ("oreRedstone", 51, "stone", "cube", False, True, 3.0, 10),
    78: ("snow", 66, "snow", "layer", True, False, 0.1, 0),
    79: ("ice", 67, "ice", "cube", True, True, 0.5, 0),
    80: ("snow", 66, "snow", "cube", False, True, 0.2, 0),
    81: ("cactus", 70, "plant", "cactus", False, True, 0.4, 0),
    82: ("clay", 72, "earth", "cube", False, True, 0.6, 0),
    83: ("reeds", 73, "plant", "cross", True, False, 0.0, 0),
    85: ("fence", 4, "wood", "fence", True, True, 2.0, 0),
    87: ("hellrock", 103, "stone", "cube", False, True, 0.4, 0),
    89: ("lightgem", 105, "glass", "cube", False, True, 0.3, 15),
    95: ("invisible_bedrock", 0, "stone", "invisible", True, True, -1.0, 0),
    96: ("trapdoor", 96, "wood", "trapdoor", True, True, 3.0, 0),
    98: ("stonebricksmooth", 54, "stone", "cube", False, True, 1.5, 0),
    102: ("thinGlass", 49, "glass", "thin_fence", True, True, 0.3, 0),
    103: ("melon", 102, "plant", "cube", False, True, 1.0, 0),
    105: ("pumpkinStem", 104, "plant", "cross", True, False, 0.0, 0),
    107: ("fenceGate", 4, "wood", "fence_gate", True, True, 2.0, 0),
    108: ("stairsBrick", 7, "stone", "stairs", False, True, 2.0, 0),
    109: ("stairsStoneBrickSmooth", 54, "stone", "stairs", False, True, 1.5, 0),
    112: ("netherBrick", 224, "stone", "cube", False, True, 2.0, 0),
    114: ("stairsNetherBrick", 224, "stone", "stairs", False, True, 2.0, 0),
    128: ("stairsSandStone", 192, "stone", "stairs", False, True, 0.8, 0),
    155: ("quartzBlock", 0, "stone", "cube", False, True, 0.8, 0),
    156: ("stairsQuartz", 0, "stone", "stairs", False, True, 0.8, 0),
    245: ("stonecutter", 0, "stone", "cube", False, True, 2.5, 0),
    246: ("glowingobsidian", 218, "stone", "cube", False, True, 10.0, 14),
    247: ("netherreactor", 234, "metal", "cube", False, True, 3.0, 0),
    248: ("info_update", 252, "earth", "cube", False, True, 1.0, 0),
    249: ("info_update", 253, "earth", "cube", False, True, 1.0, 0),
    253: ("grass", 204, "earth", "cube", False, True, 0.6, 0),
    254: ("leaves", 235, "plant", "cube", True, True, 0.2, 0),
    255: ("info_reserved6", 0, "earth", "cube", False, True, 1.0, 0),
}

BLOCKS: dict[int, Block] = {
    block_id: Block(
        block_id, name, solid, texture, shape, transparent,
        hardness, 6000000.0 if hardness < 0 else 10.0, light, material,
    )
    for block_id, (name, texture, material, shape, transparent, solid, hardness, light)
    in _TILE_ROWS.items()
}
BLOCKS[AIR] = Block(AIR, "air", False, 0, "invisible", True, 0.0, 0.0, 0, "air")

# Common legacy names retained for existing code and tests.
GRASS_BLOCK = GRASS
DIRT_BLOCK = DIRT
STONE_BLOCK = STONE
BEDROCK_BLOCK = BEDROCK

@dataclass(frozen=True)
class Face:
    """A visible axis-aligned face in chunk-local coordinates."""
    x: int
    y: int
    z: int
    direction: str
    block_id: int

class Chunk:
    """MCPE LevelChunk storage geometry: x << 11 | z << 7 | y (16x128x16)."""
    DIRECTIONS = (
        (0, 1, 0, "top"), (0, -1, 0, "bottom"),
        (1, 0, 0, "east"), (-1, 0, 0, "west"),
        (0, 0, 1, "south"), (0, 0, -1, "north"),
    )

    def __init__(self, width: int = 16, height: int = 128, depth: int = 16):
        if min(width, height, depth) <= 0:
            raise ValueError("chunk dimensions must be positive")
        if len(BLOCKS) > 256:
            raise ValueError("block IDs must fit in one byte")
        self.width, self.height, self.depth = int(width), int(height), int(depth)
        self.blocks = bytearray(self.width * self.height * self.depth)

    def _index(self, x: int, y: int, z: int) -> int:
        if not (0 <= x < self.width and 0 <= y < self.height and 0 <= z < self.depth):
            raise IndexError(f"block coordinate out of range: {(x, y, z)}")
        return (x << 11) | (z << 7) | y if self.width == 16 and self.height == 128 and self.depth == 16 else (y * self.depth + z) * self.width + x

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
        for y in range(self.height):
            for z in range(self.depth):
                row = (y * self.depth + z) * self.width
                for x in range(self.width):
                    block_id = self.blocks[self._index(x, y, z)]
                    if block_id != AIR:
                        yield x, y, z, block_id

    def visible_faces(self, neighbor: Optional["Chunk"] = None) -> Iterator[Face]:
        for x, y, z, block_id in self.iter_blocks():
            block = BLOCKS.get(block_id)
            for dx, dy, dz, direction in self.DIRECTIONS:
                nx, ny, nz = x + dx, y + dy, z + dz
                if 0 <= nx < self.width and 0 <= ny < self.height and 0 <= nz < self.depth:
                    adjacent_id = self.get(nx, ny, nz)
                    adjacent = BLOCKS.get(adjacent_id)
                    if adjacent_id != AIR and adjacent is not None and adjacent.solid and not adjacent.transparent:
                        continue
                if block is not None and block.shape in {"cross", "torch", "sign", "invisible"}:
                    if direction != "top":
                        continue
                yield Face(x, y, z, direction, block_id)

    def count_non_air(self) -> int:
        return sum(1 for value in self.blocks if value != AIR)

def generate_flat_chunk(width: int = 16, height: int = 128, depth: int = 16, ground_y: int = 8) -> Chunk:
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
