"""Pure-Python replay parser for Living Lab pickle frames.

This layer has no ROS dependency. Keep it that way. It should be usable from
notebooks, tests, conversion scripts, and ROS nodes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
import pickle

import numpy as np

from vip_hpe_core.constants.kinect import KINECT_JOINT_NAMES, KINECT_KPT_DIMS
from vip_hpe_core.constants.iwr6843 import NOISE_TARGET_IDS

def pose_3d_to_radar_plot_frame(poses: np.ndarray, scale: float = 1e-3) -> np.ndarray:
    """Convert Kinect pose coordinates to the point-cloud plotting frame.

    Input pose coordinates are assumed to be Kinect-style ``(x, y, z)`` values
    in millimetres. Output coordinates are ``(x, z, -y)`` in metres, matching
    the plotting transform in the original single-frame script.

    Args:
        poses: Array with shape ``(..., 3)`` or ``(..., 4)``. The first three
            channels are interpreted as x/y/z. If a confidence channel exists,
            it is preserved as the fourth channel.
        scale: Scale factor from source units to metres.

    Returns:
        Array with the same leading dimensions. Coordinate channels are in
        metres. Confidence is preserved if present.
    """
    arr = np.asarray(poses, dtype=np.float32).copy()
    xyz = arr[..., [0, 2, 1]]
    xyz[..., 2] *= -1.0
    xyz *= scale
    if arr.shape[-1] >= 4:
        return np.concatenate([xyz, arr[..., 3:4]], axis=-1)
    return xyz


@dataclass(frozen=True)
class LivingLabFrame:
    """Parsed replay frame.

    ``pc`` has shape ``(N_points, 6)`` with columns:
    ``x, y, z, doppler, snr, target_id``.

    ``poses_3d_gt`` is either ``None`` or has shape
    ``(N_people, N_joints, 4)`` with ``x, y, z, confidence``.
    """

    frame_index: int
    pc: np.ndarray
    poses_3d_gt: Optional[np.ndarray]
    source_timestamp: float = 0.0

    @property
    def px(self) -> np.ndarray:
        return self.pc[:, 0]

    @property
    def py(self) -> np.ndarray:
        return self.pc[:, 1]

    @property
    def pz(self) -> np.ndarray:
        return self.pc[:, 2]

    @property
    def pd(self) -> np.ndarray:
        return self.pc[:, 3]

    @property
    def ps(self) -> np.ndarray:
        return self.pc[:, 4]

    @property
    def tid(self) -> np.ndarray:
        return self.pc[:, 5]


def _extract_source_timestamp(raw_frame: dict[str, Any], fallback: float) -> float:
    """Best-effort timestamp extraction from heterogeneous pickle frames."""
    for key in ('timestamp', 'time', 't', 'frame_time', 'unix_time', 'source_timestamp'):
        value = raw_frame.get(key)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                pass
    return float(fallback)


class LivingLabSubjectReplay:
    """Loads and indexes a pickled Living Lab subject/session."""

    def __init__(self, path: str | Path, gtrack_filtering: bool = True, fps_fallback: float = 10.0):
        self.path = Path(path).expanduser()
        self.gtrack_filtering = bool(gtrack_filtering)
        self.fps_fallback = float(fps_fallback)
        self.data = self._load_pickled_subject()

    def _load_pickled_subject(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            raise FileNotFoundError(f'Pickle file does not exist: {self.path}')
        with self.path.open('rb') as handle:
            data = pickle.load(handle)
        if not isinstance(data, (list, tuple)):
            raise TypeError(f'Expected pickle to contain a list/tuple of frames. Got: {type(data)!r}')
        return list(data)

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> LivingLabFrame:
        raw = self.data[idx]
        if not isinstance(raw, dict):
            raise TypeError(f'Frame {idx} is not a dict. Got: {type(raw)!r}')
        pc = self._parse_pc(raw)
        pose = self._parse_3d_gt_pose(raw)
        timestamp = _extract_source_timestamp(raw, fallback=idx / self.fps_fallback)
        return LivingLabFrame(frame_index=int(idx), pc=pc, poses_3d_gt=pose, source_timestamp=timestamp)

    def _parse_pc(self, raw_frame: dict[str, Any]) -> np.ndarray:
        if 'pc' not in raw_frame:
            raise KeyError('Replay frame does not contain key "pc"')
        pc = np.asarray(raw_frame['pc'], dtype=np.float32)
        if pc.size == 0:
            return np.zeros((0, 6), dtype=np.float32)
        pc = pc.reshape(-1, pc.shape[-1])
        if pc.shape[1] < 6:
            raise ValueError(f'Expected point cloud to have at least 6 columns. Got shape: {pc.shape}')
        pc = pc[:, :6]
        if self.gtrack_filtering:
            target_ids = pc[:, 5].astype(np.int32)
            mask_noise = np.isin(target_ids, NOISE_TARGET_IDS)
            pc = pc[~mask_noise]
        return pc.astype(np.float32, copy=False)

    def _parse_3d_gt_pose(self, raw_frame: dict[str, Any]) -> Optional[np.ndarray]:
        poses3d = raw_frame.get('poses3d')
        if poses3d is None:
            return None
        poses3d = np.asarray(poses3d, dtype=np.float32)
        if poses3d.size == 0:
            return None

        n_joints = len(KINECT_JOINT_NAMES)
        n_dims = len(KINECT_KPT_DIMS)
        expected_width = n_joints * n_dims

        # The original script reshaped directly to (-1, 32, 4). This keeps that
        # behaviour, but emits a clearer error if the frame has an unexpected shape.
        if poses3d.size % expected_width != 0:
            raise ValueError(
                f'Cannot reshape poses3d with shape {poses3d.shape} into '
                f'(-1, {n_joints}, {n_dims}). Total size {poses3d.size} is not '
                f'a multiple of {expected_width}.'
            )
        pose = poses3d.reshape(-1, n_joints, n_dims)
        return pose_3d_to_radar_plot_frame(pose)
