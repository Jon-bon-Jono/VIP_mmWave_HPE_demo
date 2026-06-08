from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class ModelInputSpec:
    """
    Describes the model input produced by a preprocessor.

    This is deliberately NumPy/Python-only so that ROS runtime code and
    PyTorch training code can both depend on it.
    """

    name: str
    version: str
    shape: tuple[int | None, ...]
    dtype: str
    channels: tuple[str, ...] = ()
    coordinate_frame: str = "unknown"


@dataclass(frozen=True)
class PreprocessorOutput:
    """
    Output from a point-cloud preprocessor.

    array:
        NumPy model input. For example, this might be (C, H, W), (N, F),
        or any other model-specific representation.

    metadata:
        Lightweight metadata useful for debugging, evaluation, batching,
        or converting model outputs back to world/radar coordinates.
    """

    array: NDArray[np.float32]
    metadata: dict[str, Any] = field(default_factory=dict)


class BasePointCloudPreprocessor(ABC):
    """
    Base class for point-cloud-to-model-input preprocessing.

    Implementations must be deterministic unless explicitly configured
    otherwise. Training-only augmentation should not live here.
    """

    name: str = "base"
    version: str = "0.0.0"

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = dict(config or {})

    @property
    @abstractmethod
    def output_spec(self) -> ModelInputSpec:
        """Return the output contract for this preprocessor."""
        raise NotImplementedError

    @abstractmethod
    def transform(
        self,
        points_np: NDArray[np.number],
        *,
        frame_metadata: dict[str, Any] | None = None,
    ) -> PreprocessorOutput:
        """
        Convert one point-cloud frame into one model input.

        points_np:
            NumPy point cloud array. The expected column convention should be
            documented by the concrete preprocessor.

        frame_metadata:
            Optional per-frame metadata such as frame index, timestamp, or
            recording/session ID.

        returns:
            PreprocessorOutput containing the model input as a NumPy array.
        """
        raise NotImplementedError

    def batch_transform(
        self,
        frames: list[NDArray[np.number]],
        *,
        metadata: list[dict[str, Any] | None] | None = None,
    ) -> list[PreprocessorOutput]:
        """
        Apply transform() to a list of frames.

        This stays NumPy-only. PyTorch conversion should happen in ml/.
        """
        if metadata is None:
            metadata = [None] * len(frames)

        if len(frames) != len(metadata):
            raise ValueError("frames and metadata must have the same length")

        return [
            self.transform(frame, frame_metadata=frame_meta)
            for frame, frame_meta in zip(frames, metadata)
        ]