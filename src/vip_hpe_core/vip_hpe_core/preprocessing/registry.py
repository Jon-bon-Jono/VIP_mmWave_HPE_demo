from __future__ import annotations

from typing import Any

import rclpy


from vip_hpe_core.preprocessing.base import BasePointCloudPreprocessor
from vip_hpe_core.preprocessing.model_input import DummyPointCloudPreprocessor


_PREPROCESSOR_REGISTRY: dict[str, type[BasePointCloudPreprocessor]] = {
    DummyPointCloudPreprocessor.name: DummyPointCloudPreprocessor,
}


def available_preprocessors() -> tuple[str, ...]:
    return tuple(sorted(_PREPROCESSOR_REGISTRY.keys()))


def build_preprocessor(config: dict[str, Any]) -> BasePointCloudPreprocessor:
    """
    Build a preprocessor from a config dictionary.

    Expected format:
        {
            "name": "dummy_pointcloud",
            "params": {
                "expected_num_features": 6
            }
        }
    """
    if "name" not in config:
        raise ValueError("Preprocessor config must contain a 'name' field")

    name = str(config["name"])
    params = dict(config.get("params", {}))

    if name not in _PREPROCESSOR_REGISTRY:
        raise ValueError(
            f"Unknown preprocessor '{name}'. "
            f"Available: {available_preprocessors()}"
        )

    return _PREPROCESSOR_REGISTRY[name](params)