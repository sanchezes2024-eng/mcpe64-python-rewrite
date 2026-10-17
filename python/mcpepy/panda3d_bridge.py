"""Optional Panda3D backend using the repository's original terrain atlas.

This is a clean-room adapter over the Python voxel model. Block UVs are selected
from data/images/terrain.png; the original atlas is used directly at runtime.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .chunkmesh import build_world_mesh
from .voxel import AIR, BLOCKS, BEDROCK, DIRT, GRASS, STONE
from .world import World

ROOT = Path(__file__).resolve().parents[2]
ASSET_ROOT = ROOT / "data" / "images"

# Original MCPE terrain atlas is a 16-by-16 grid of 16-pixel tiles.
# Coordinates are (column, row), counted from the top-left of terrain.png.
# Grass uses different tiles on its top and sides.
# Every registered native Tile ID uses the texture index recorded by Tile.cpp.
# The MCPE atlas is a 16x16 grid. Subclass-specific face selection (logs,
# sandstone, grass, stone bricks, etc.) is added below where the source is known.
TERRAIN_TILES = {
    block_id: {"all": (block.texture % 16, block.texture // 16)}
    for block_id, block in BLOCKS.items()
    if block_id != AIR and block.shape not in {"invisible"}
}
TERRAIN_TILES[GRASS] = {"top": (0, 0), "bottom": (2, 0), "side": (3, 0)}
TERRAIN_TILES[17] = {"top": (5, 1), "bottom": (5, 1), "side": (4, 1)}
TERRAIN_TILES[18] = {"all": (4, 3)}
TERRAIN_TILES[24] = {"top": (0, 12), "bottom": (0, 12), "side": (5, 14)}
TERRAIN_TILES[98] = {"top": (6, 3), "bottom": (6, 3), "side": (4, 6)}
TERRAIN_TILES[155] = {"all": (0, 0)}

