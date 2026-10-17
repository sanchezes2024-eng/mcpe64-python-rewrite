"""Port of ExternalFileLevelStorageSource's world-directory and level.dat metadata flow.

The native client stores worlds in <externalPath>/games/com.mojang/minecraftWorlds/<id>.
Each level.dat begins with two little-endian int32 values (storage version and payload
length), followed by the native NBT compound payload. This module implements the
metadata subset used by LevelSummary and new-world creation; it does not claim to
load native chunks.dat yet.
"""
from __future__ import annotations

import os
import re
import struct
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ILLEGAL_FILE_CHARACTERS = "/\n\r\t\0\f`?*\\<>|\":""
TEMP_LEVEL_ID = "_LastJoinedServer"


@dataclass(frozen=True)
class LevelSummary:
    id: str
    name: str
    last_played: int
    game_type: int
    size_on_disk: int


def worlds_path() -> Path:
    """Resolve the native external storage root, with an override for testing."""
    override = os.environ.get("MCPEPY_WORLDS_DIR")
    if override:
        return Path(override).expanduser()
    external = Path(os.environ.get("MCPEPY_EXTERNAL_STORAGE", str(Path.home())))
    return external / "games" / "com.mojang" / "minecraftWorlds"


def _read_exact(stream, size: int) -> bytes:
    data = stream.read(size)
    if len(data) != size:
        raise ValueError("truncated NBT payload")
    return data


def _read_string(stream) -> str:
    size = struct.unpack(">H", _read_exact(stream, 2))[0]
    return _read_exact(stream, size).decode("utf-8", "replace")


def _read_payload(stream, tag_type: int) -> Any:
    if tag_type == 1:
        return struct.unpack(">b", _read_exact(stream, 1))[0]
    if tag_type == 2:
        return struct.unpack(">h", _read_exact(stream, 2))[0]
    if tag_type == 3:
        return struct.unpack(">i", _read_exact(stream, 4))[0]
    if tag_type == 4:
        return struct.unpack(">q", _read_exact(stream, 8))[0]
    if tag_type == 5:
        return struct.unpack(">f", _read_exact(stream, 4))[0]
    if tag_type == 6:
        return struct.unpack(">d", _read_exact(stream, 8))[0]
    if tag_type == 7:
        length = struct.unpack(">i", _read_exact(stream, 4))[0]
        if length < 0 or length > 64 * 1024 * 1024:
            raise ValueError("invalid NBT byte-array length")
        return _read_exact(stream, length)
    if tag_type == 8:
        return _read_string(stream)
    if tag_type == 9:
        child_type = struct.unpack(">B", _read_exact(stream, 1))[0]
        length = struct.unpack(">i", _read_exact(stream, 4))[0]
        if length < 0 or length > 1_000_000:
            raise ValueError("invalid NBT list length")
        return [_read_payload(stream, child_type) for _ in range(length)]
    if tag_type == 10:
        result = {}
        while True:
            child_type = struct.unpack(">B", _read_exact(stream, 1))[0]
            if child_type == 0:
                return result
            name = _read_string(stream)
            result[name] = _read_payload(stream, child_type)
    if tag_type == 11:
        length = struct.unpack(">i", _read_exact(stream, 4))[0]
        if length < 0 or length > 16 * 1024 * 1024:
            raise ValueError("invalid NBT int-array length")
        return list(struct.unpack(">" + "i" * length, _read_exact(stream, 4 * length)))
    if tag_type == 12:
        length = struct.unpack(">i", _read_exact(stream, 4))[0]
        if length < 0 or length > 16 * 1024 * 1024:
            raise ValueError("invalid NBT long-array length")
        return list(struct.unpack(">" + "q" * length, _read_exact(stream, 8 * length)))
    raise ValueError("unsupported NBT tag type %d" % tag_type)


def read_level_dat(directory: Path) -> tuple[int, dict[str, Any]] | None:
    """Read level.dat, falling back to level.dat_old as the C++ loader does."""
    for filename in ("level.dat", "level.dat_old"):
        try:
            with (directory / filename).open("rb") as stream:
                version, size = struct.unpack("<ii", _read_exact(stream, 8))
                if size <= 0 or size > 64 * 1024 * 1024:
                    continue
                payload = _read_exact(stream, size)
                if version == 1:
                    # Native v1 uses RakNet bit serialization, not NBT.
                    continue
                import io
                nbt = io.BytesIO(payload)
                root_type = struct.unpack(">B", _read_exact(nbt, 1))[0]
                if root_type != 10:
                    continue
                _read_string(nbt)  # root name
                tag = _read_payload(nbt, root_type)
                if isinstance(tag, dict):
                    return version, tag
        except (OSError, ValueError, struct.error):
            continue
    return None


def list_worlds(root: Path | None = None) -> list[LevelSummary]:
    """Mirror ExternalFileLevelStorageSource::getLevelList and LevelSummary ordering."""
    root = Path(root) if root is not None else worlds_path()
    summaries = []
    try:
        entries = list(root.iterdir())
    except OSError:
        return summaries
    for entry in entries:
        if not entry.is_dir():
            continue
        loaded = read_level_dat(entry)
        if loaded is None:
            continue
        _, data = loaded
        summaries.append(LevelSummary(
            id=entry.name,
            name=str(data.get("LevelName", entry.name)),
            last_played=int(data.get("LastPlayed", 0)),
            game_type=int(data.get("GameType", 1)),
            size_on_disk=int(data.get("SizeOnDisk", 0)),
        ))
    return sorted(summaries, key=lambda item: item.last_played, reverse=True)


def unique_level_id(name: str, summaries: list[LevelSummary]) -> str:
    """Match the native getUniqueLevelName rule: append '-' until unused."""
    used = {summary.id for summary in summaries}
    result = name
    while result in used:
        result += "-"
    return result


def _tag(tag_type: int, name: str, payload: bytes) -> bytes:
    encoded = name.encode("utf-8")
    if len(encoded) > 65535:
        raise ValueError("NBT name is too long")
    return struct.pack(">BH", tag_type, len(encoded)) + encoded + payload


def _int_tag(name: str, value: int) -> bytes:
    return _tag(3, name, struct.pack(">i", int(value)))


def _long_tag(name: str, value: int) -> bytes:
    return _tag(4, name, struct.pack(">q", int(value)))


def _string_tag(name: str, value: str) -> bytes:
    encoded = value.encode("utf-8")
    return _tag(8, name, struct.pack(">H", len(encoded)) + encoded)


def write_level_dat(directory: Path, *, seed: int, game_type: int, name: str) -> None:
    """Write a native version-2 level.dat metadata compound using LevelData keys."""
    directory.mkdir(parents=True, exist_ok=True)
    now = int(time.time())
    body = b"".join((
        _long_tag("RandomSeed", seed),
        _int_tag("GameType", game_type),
        _int_tag("SpawnX", 128),
        _int_tag("SpawnY", 64),
        _int_tag("SpawnZ", 128),
        _long_tag("Time", 0),
        _long_tag("SizeOnDisk", 0),
        _long_tag("LastPlayed", now),
        _string_tag("LevelName", name),
        _int_tag("StorageVersion", 2),
        _int_tag("Platform", 2),
        b"\\x00",
    ))
    root_tag = b"\\x0a\\x00\\x00" + body
    payload = struct.pack("<ii", 2, len(root_tag)) + root_tag
    target = directory / "level.dat"
    temp = directory / "level.dat_new"
    backup = directory / "level.dat_old"
    temp.write_bytes(payload)
    if target.exists():
        try:
            backup.unlink()
        except FileNotFoundError:
            pass
        target.replace(backup)
    temp.replace(target)


def create_world(name: str, seed: int, game_type: int, root: Path | None = None) -> LevelSummary:
    """Create the native world directory and level.dat metadata."""
    root = Path(root) if root is not None else worlds_path()
    root.mkdir(parents=True, exist_ok=True)
    display_name = name.strip() or "My World"
    level_id = display_name
    for char in ILLEGAL_FILE_CHARACTERS:
        level_id = level_id.replace(char, "")
    level_id = unique_level_id(level_id, list_worlds(root))
    if not level_id:
        level_id = unique_level_id("My World", list_worlds(root))
    directory = root / level_id
    directory.mkdir(parents=True, exist_ok=False)
    write_level_dat(directory, seed=seed, game_type=game_type, name=display_name)
    return LevelSummary(level_id, display_name, int(time.time()), int(game_type), 0)
