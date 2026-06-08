from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any

import yaml


_PATH_KEYS = {
    "pickle_path",
    "model_path",
    "preprocessor_config_path",
    "output_dir",
    "recording_dir",
    "camera_path",
    "video_path",
}


def _expand_path(path_value: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(path_value)))


def _resolve_path(path_value: str, *, workspace_root: Path) -> str:
    path = _expand_path(path_value)

    if not path.is_absolute():
        path = workspace_root / path

    return str(path.resolve())


def _resolve_known_paths(obj: Any, *, workspace_root: Path) -> Any:
    """
    Recursively resolve values for known path-like keys.

    This intentionally does not resolve every string, because topics such as
    /radar/points are also strings and should not be treated as file paths.
    """
    if isinstance(obj, dict):
        resolved = {}
        for key, value in obj.items():
            if key in _PATH_KEYS and isinstance(value, str) and value:
                resolved[key] = _resolve_path(value, workspace_root=workspace_root)
            else:
                resolved[key] = _resolve_known_paths(value, workspace_root=workspace_root)
        return resolved

    if isinstance(obj, list):
        return [_resolve_known_paths(v, workspace_root=workspace_root) for v in obj]

    return obj


def load_session_config(path: str | Path) -> dict[str, Any]:
    """
    Load and normalise a YAML runtime session config.

    Relative paths inside the YAML are resolved relative to session.workspace_root
    if provided, otherwise relative to the current working directory.
    """
    config_path = _expand_path(str(path)).resolve()

    if not config_path.exists():
        raise FileNotFoundError(f"Session config does not exist: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    if cfg is None:
        raise ValueError(f"Session config is empty: {config_path}")

    if not isinstance(cfg, dict):
        raise TypeError(f"Session config must be a YAML mapping/dictionary: {config_path}")

    cfg = copy.deepcopy(cfg)

    session_cfg = cfg.setdefault("session", {})
    if not isinstance(session_cfg, dict):
        raise TypeError("'session' must be a mapping/dictionary")

    workspace_root_raw = session_cfg.get("workspace_root", ".")
    workspace_root = _expand_path(str(workspace_root_raw))
    if not workspace_root.is_absolute():
        workspace_root = Path.cwd() / workspace_root
    workspace_root = workspace_root.resolve()

    cfg["_config_path"] = str(config_path)
    cfg["_config_dir"] = str(config_path.parent)
    cfg["_workspace_root"] = str(workspace_root)

    cfg = _resolve_known_paths(cfg, workspace_root=workspace_root)

    return cfg