"""Reader/writer for MCPE 0.6.1 RegionFile chunks.dat.

Format transcribed from src/world/level/storage/RegionFile.cpp and
ExternalFileLevelStorage.cpp. The 4 KiB header is 1024 little-endian int32
sector offsets. Each offset packs (sector index << 8) | sector count.
Chunk payload is raw LevelChunk arrays, not NBT or Anvil compression.
"""
from __future__ import annotations

import os
import struct
from pathlib import Path
from typing import NamedTuple

SECTOR_BYTES = 4096
SECTOR_INTS = SECTOR_BYTES // 4
SECTOR_COLS = 32
CHUNK_BLOCK_COUNT = 16 * 16 * 128
CHUNK_COLUMNS = 16 * 16
NIBBLE_ARRAY_BYTES = CHUNK_BLOCK_COUNT // 2
CHUNK_PAYLOAD_BYTES = CHUNK_BLOCK_COUNT + 3 * NIBBLE_ARRAY_BYTES + CHUNK_COLUMNS


class NativeChunkData(NamedTuple):
    blocks: bytes
    data: bytes
    sky_light: bytes
    block_light: bytes
    update_map: bytes


def decode_chunk_payload(payload: bytes) -> NativeChunkData:
    """Decode the exact byte-array sequence written by ExternalFileLevelStorage::save."""
    if len(payload) < CHUNK_PAYLOAD_BYTES:
        raise ValueError(
            f"truncated MCPE chunk payload: {len(payload)} < {CHUNK_PAYLOAD_BYTES}"
        )
    offset = 0
    blocks = payload[offset:offset + CHUNK_BLOCK_COUNT]
    offset += CHUNK_BLOCK_COUNT
    data = payload[offset:offset + NIBBLE_ARRAY_BYTES]
    offset += NIBBLE_ARRAY_BYTES
    sky = payload[offset:offset + NIBBLE_ARRAY_BYTES]
    offset += NIBBLE_ARRAY_BYTES
    block = payload[offset:offset + NIBBLE_ARRAY_BYTES]
    offset += NIBBLE_ARRAY_BYTES
    update = payload[offset:offset + CHUNK_COLUMNS]
    return NativeChunkData(blocks, data, sky, block, update)


def encode_chunk_payload(chunk: NativeChunkData) -> bytes:
    """Encode the exact byte-array order used by ExternalFileLevelStorage::save."""
    expected = (
        ("blocks", chunk.blocks, CHUNK_BLOCK_COUNT),
        ("data", chunk.data, NIBBLE_ARRAY_BYTES),
        ("sky_light", chunk.sky_light, NIBBLE_ARRAY_BYTES),
        ("block_light", chunk.block_light, NIBBLE_ARRAY_BYTES),
        ("update_map", chunk.update_map, CHUNK_COLUMNS),
    )
    for name, value, size in expected:
        if len(value) != size:
            raise ValueError(f"{name} must be {size} bytes, got {len(value)}")
    return b"".join(value for _, value, _ in expected)


class RegionFile:
    """Native 32x32 chunk region backed by a chunks.dat file."""

    def __init__(self, world_directory: str | os.PathLike[str]):
        self.path = Path(world_directory) / "chunks.dat"
        self.offsets = [0] * SECTOR_INTS
        self.sector_free: dict[int, bool] = {0: False}
        self._opened = False

    @staticmethod
    def _index(x: int, z: int) -> int:
        if not (0 <= x < SECTOR_COLS and 0 <= z < SECTOR_COLS):
            raise ValueError("native region chunk coordinates must be in 0..31")
        return x + z * SECTOR_COLS

    def open(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_bytes(bytes(SECTOR_BYTES))
        raw = self.path.read_bytes()
        if len(raw) < SECTOR_BYTES:
            raise ValueError("chunks.dat is shorter than its 4 KiB header")
        self.offsets = list(struct.unpack("<1024I", raw[:SECTOR_BYTES]))
        self.sector_free = {0: False}
        sector_count = (len(raw) + SECTOR_BYTES - 1) // SECTOR_BYTES
        for offset in self.offsets:
            if not offset:
                continue
            base, count = offset >> 8, offset & 0xFF
            if base < 1 or count < 1 or base + count > sector_count:
                continue
            for sector in range(base, base + count):
                self.sector_free[sector] = False
        self._opened = True
        return True

    def read_chunk(self, x: int, z: int) -> bytes | None:
        if not self._opened:
            self.open()
        offset = self.offsets[self._index(x, z)]
        if offset == 0:
            return None
        sector, count = offset >> 8, offset & 0xFF
        raw = self.path.read_bytes()
        start = sector * SECTOR_BYTES
        if sector < 1 or count < 1 or start + 4 > len(raw):
            return None
        length = struct.unpack_from("<I", raw, start)[0]
        if length < 4 or length > count * SECTOR_BYTES:
            return None
        end = start + length
        if end > len(raw):
            return None
        return raw[start + 4:end]

    def write_chunk(self, x: int, z: int, payload: bytes) -> None:
        if not self._opened:
            self.open()
        index = self._index(x, z)
        record_size = len(payload) + 4
        # Match RegionFile.cpp: sectorsNeeded = (size / sector) + 1.
        sectors_needed = record_size // SECTOR_BYTES + 1
        if sectors_needed > 255:
            raise ValueError("native region chunk exceeds the 255-sector limit")
        old = self.offsets[index]
        old_sector, old_count = old >> 8, old & 0xFF
        if old_sector and old_count == sectors_needed:
            slot = old_sector
        else:
            for sector in range(old_sector, old_sector + old_count):
                if sector > 0:
                    self.sector_free[sector] = True
            slot = 1
            while not all(self.sector_free.get(slot + i, True) for i in range(sectors_needed)):
                slot += 1
            for sector in range(slot, slot + sectors_needed):
                self.sector_free[sector] = False
            self.offsets[index] = (slot << 8) | sectors_needed

        record = struct.pack("<I", record_size) + payload
        record += bytes(sectors_needed * SECTOR_BYTES - len(record))
        with self.path.open("r+b") as stream:
            stream.seek(slot * SECTOR_BYTES)
            stream.write(record)
            stream.seek(0)
            stream.write(struct.pack("<1024I", *self.offsets))
        self.sector_free[0] = False

    def iter_chunks(self):
        """Yield (chunk_x, chunk_z, raw_payload) for all valid stored chunks."""
        if not self._opened:
            self.open()
        for z in range(SECTOR_COLS):
            for x in range(SECTOR_COLS):
                if self.offsets[x + z * SECTOR_COLS]:
                    payload = self.read_chunk(x, z)
                    if payload is not None:
                        yield x, z, payload

    def load_into_world(self, world) -> int:
        """Copy native block arrays into a compatible 16x128x16 World.

        Returns the number of chunks loaded. Light and metadata arrays are
        parsed and validated, but the current World model stores only block IDs.
        """
        if (world.chunk_width, world.chunk_height, world.chunk_depth) != (16, 128, 16):
            raise ValueError("native MCPE chunks require 16x128x16 world chunks")
        loaded = 0
        for x, z, payload in self.iter_chunks():
            native = decode_chunk_payload(payload)
            chunk = world.get_chunk(x, z, create=True)
            chunk.blocks[:] = native.blocks
            loaded += 1
        return loaded

    def close(self) -> None:
        self._opened = False
