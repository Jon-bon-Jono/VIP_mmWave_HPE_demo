"""Matplotlib 3D visualisation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import matplotlib.pyplot as plt

from vip_hpe_core.constants.living_lab import ROOM_BOUNDS
from vip_hpe_core.constants.kinect import KINECT_JOINT_NAMES, KINECT_LIMB_CONNECTIONS


@dataclass
class PlotFrame:
    frame_index: int
    pc: np.ndarray
    pose: Optional[np.ndarray]


class AnimatedPosePointCloudPlot:
    """Stateful animated 3D plot for replayed radar points and 3D poses."""

    def __init__(self, figsize=(8, 6), boundless: bool = False, pc_alpha: float = 0.1):
        self.fig = plt.figure(figsize=figsize)
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.boundless = boundless
        self.pc_alpha = pc_alpha
        self.name_to_idx = {n: i for i, n in enumerate(KINECT_JOINT_NAMES)}
        plt.ion()
        self.fig.show()

    def draw(self, frame: PlotFrame):
        self.ax.clear()
        self.ax.set_title(f'mmWave 3D Point Cloud with Human Pose | frame {frame.frame_index}')
        self.ax.set_xlabel('x (m)')
        self.ax.set_ylabel('y (m)')
        self.ax.set_zlabel('z (m)')

        pc = frame.pc
        if pc is not None and pc.size > 0:
            self.ax.scatter(pc[:, 0], pc[:, 1], pc[:, 2], c='r', s=1, alpha=self.pc_alpha)

        pose = frame.pose
        if pose is not None and pose.size > 0:
            self.ax.scatter(pose[..., 0].ravel(), pose[..., 1].ravel(), pose[..., 2].ravel(), c='b', s=5)
            for person_idx in range(pose.shape[0]):
                for left_name, right_name in KINECT_LIMB_CONNECTIONS:
                    i = self.name_to_idx[left_name]
                    j = self.name_to_idx[right_name]
                    self.ax.plot(
                        [pose[person_idx, i, 0], pose[person_idx, j, 0]],
                        [pose[person_idx, i, 1], pose[person_idx, j, 1]],
                        [pose[person_idx, i, 2], pose[person_idx, j, 2]],
                        c='b',
                        linewidth=1,
                    )

        if not self.boundless:
            self.ax.set_xlim(*ROOM_BOUNDS[0])
            self.ax.set_ylim(*ROOM_BOUNDS[1])
            self.ax.set_zlim(*ROOM_BOUNDS[2])

        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()
        plt.pause(0.001)
