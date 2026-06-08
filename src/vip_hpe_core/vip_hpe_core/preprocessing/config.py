from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from vip_hpe_core.preprocessing.base import BasePointCloudPreprocessor
from vip_hpe_core.preprocessing.registry import build_preprocessor


def load_preprocessor_config(path: str | Path) -> dict[str, Any]:
    """
    Load a point-cloud preprocessor YAML config.

    Expected YAML format:

        name: dummy_pointcloud
        params:
          expected_num_features: 6
          copy: true
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Preprocessor config does not exist: {path}")

    with path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    if cfg is None:
        raise ValueError(f"Preprocessor config is empty: {path}")

    if not isinstance(cfg, dict):
        raise TypeError(f"Preprocessor config must be a YAML mapping: {path}")

    return cfg


def build_preprocessor_from_yaml(path: str | Path) -> BasePointCloudPreprocessor:
    """
    Load a YAML config and instantiate the requested point-cloud preprocessor.
    """
    cfg = load_preprocessor_config(path)
    return build_preprocessor(cfg)