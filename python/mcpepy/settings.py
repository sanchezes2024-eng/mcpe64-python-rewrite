"""Persistent user options for the MCPE Python prototype."""
from __future__ import annotations

import json
import os
from pathlib import Path


DEFAULT_OPTIONS = {
    "mouse_sensitivity": 0.0025,
    "invert_y": False,
    "show_fps": False,
}


def options_path() -> Path:
    override = os.environ.get("MCPEPY_CONFIG_DIR")
    base = Path(override).expanduser() if override else Path.home() / ".mcpepy"
    return base / "options.json"


def load_options() -> dict:
    result = dict(DEFAULT_OPTIONS)
    try:
        raw = json.loads(options_path().read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            sensitivity = float(raw.get("mouse_sensitivity", result["mouse_sensitivity"]))
            if 0.0005 <= sensitivity <= 0.01:
                result["mouse_sensitivity"] = sensitivity
            result["invert_y"] = bool(raw.get("invert_y", result["invert_y"]))
            result["show_fps"] = bool(raw.get("show_fps", result["show_fps"]))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        pass
    return result


def save_options(options: dict) -> None:
    validated = dict(DEFAULT_OPTIONS)
    sensitivity = float(options.get("mouse_sensitivity", DEFAULT_OPTIONS["mouse_sensitivity"]))
    if not 0.0005 <= sensitivity <= 0.01:
        raise ValueError("mouse sensitivity must be between 0.0005 and 0.01")
    validated["mouse_sensitivity"] = sensitivity
    validated["invert_y"] = bool(options.get("invert_y", False))
    validated["show_fps"] = bool(options.get("show_fps", False))
    path = options_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".json.tmp")
    temp.write_text(json.dumps(validated, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)
