from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray

from vip_hpe_core.preprocessing.base import (
    BasePointCloudPreprocessor,
    ModelInputSpec,
    PreprocessorOutput,
)


class DummyPointCloudPreprocessor(BasePointCloudPreprocessor):
    """
    Minimal placeholder preprocessor.

    This is intentionally simple. It demonstrates the expected interface:
    a preprocessor receives one point-cloud frame as a NumPy array and returns
    one NumPy model input plus metadata.

    It does not change the geometry. It only casts to float32 and optionally
    copies the input.
    """

    name = "dummy_pointcloud"
    version = "0.1.0"

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)

        self.copy = bool(self.config.get("copy", True))
        self.expected_num_features = self.config.get("expected_num_features", None)

    @property
    def output_spec(self) -> ModelInputSpec:
        feature_dim = self.expected_num_features
        return ModelInputSpec(
            name=self.name,
            version=self.version,
            shape=(None, feature_dim),
            dtype="float32",
            channels=(),
            coordinate_frame="radar_cartesian",
        )

    def transform(
        self,
        points_np: NDArray[np.number],
        *,
        frame_metadata: dict[str, Any] | None = None,
    ) -> PreprocessorOutput:
        if not isinstance(points_np, np.ndarray):
            raise TypeError(f"points_np must be a NumPy array, got {type(points_np)}")

        if points_np.ndim != 2:
            raise ValueError(
                f"points_np must have shape (num_points, num_features), "
                f"got {points_np.shape}"
            )

        if self.expected_num_features is not None:
            if points_np.shape[1] != int(self.expected_num_features):
                raise ValueError(
                    f"Expected {self.expected_num_features} point features, "
                    f"got {points_np.shape[1]}"
                )

        array = points_np.astype(np.float32, copy=self.copy)

        metadata = dict(frame_metadata or {})
        metadata.update(
            {
                "preprocessor_name": self.name,
                "preprocessor_version": self.version,
                "num_points": int(points_np.shape[0]),
                "num_features": int(points_np.shape[1]),
            }
        )

        return PreprocessorOutput(array=array, metadata=metadata)


# Temporary backwards-compatible alias if existing code imports this name.
PointCloudPreprocessor = DummyPointCloudPreprocessor


class PointCloudPreprocessor:
    def __init__(self, config):
        self.config = config

    def transform(self, points_np):
        # TODO: convert point cloud array to model input tensor
        """
        points_np: NumPy array containing point cloud fields.
        returns: NumPy array in the exact format expected by the pose model.
        """
        return points_np