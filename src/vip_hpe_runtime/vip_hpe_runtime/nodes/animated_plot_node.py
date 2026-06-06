"""Animated Matplotlib subscriber node.

This is deliberately not a direct pickle plotter. It subscribes to replay/runtime
ROS topics so the same visualisation can later be used with live radar and live
model inference.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Optional

import rclpy
from rclpy.node import Node

from vip_hpe_msgs.msg import RadarFrame, PersonPose3DArray
from vip_hpe_runtime.adapters.ros_conversions import radar_msg_to_numpy, pose_msg_to_numpy
from vip_hpe_runtime.visualization.plotter import AnimatedPosePointCloudPlot, PlotFrame


class AnimatedPlotNode(Node):
    def __init__(self):
        super().__init__('animated_plot_node')
        self.declare_parameter('radar_topic', '/radar/points')
        self.declare_parameter('pose_topic', '/pose/people')
        self.declare_parameter('redraw_hz', 20.0)
        self.declare_parameter('boundless', False)
        self.declare_parameter('pc_alpha', 0.1)
        self.declare_parameter('require_matching_indices', False)

        radar_topic = self.get_parameter('radar_topic').get_parameter_value().string_value
        pose_topic = self.get_parameter('pose_topic').get_parameter_value().string_value
        redraw_hz = self.get_parameter('redraw_hz').get_parameter_value().double_value
        boundless = self.get_parameter('boundless').get_parameter_value().bool_value
        pc_alpha = self.get_parameter('pc_alpha').get_parameter_value().double_value
        self.require_matching_indices = self.get_parameter('require_matching_indices').get_parameter_value().bool_value

        self.plotter = AnimatedPosePointCloudPlot(boundless=boundless, pc_alpha=pc_alpha)
        self.latest_pc = None
        self.latest_pc_index = None
        self.latest_pose = None
        self.latest_pose_index = None
        self.last_drawn = None

        self.create_subscription(RadarFrame, radar_topic, self._on_radar, 10)
        self.create_subscription(PersonPose3DArray, pose_topic, self._on_pose, 10)
        self.create_timer(1.0 / max(float(redraw_hz), 1e-6), self._on_timer)
        self.get_logger().info(f'Animated plot subscribed to {radar_topic} and {pose_topic}')

    def _on_radar(self, msg: RadarFrame):
        self.latest_pc = radar_msg_to_numpy(msg)
        self.latest_pc_index = int(msg.frame_index)

    def _on_pose(self, msg: PersonPose3DArray):
        self.latest_pose = pose_msg_to_numpy(msg)
        self.latest_pose_index = int(msg.frame_index)

    def _on_timer(self):
        if self.latest_pc is None:
            return
        if self.require_matching_indices and self.latest_pose_index != self.latest_pc_index:
            return
        frame_index = int(self.latest_pc_index)
        if self.last_drawn == frame_index:
            return
        self.plotter.draw(PlotFrame(frame_index=frame_index, pc=self.latest_pc, pose=self.latest_pose))
        self.last_drawn = frame_index


def main(args=None):
    rclpy.init(args=args)
    node = AnimatedPlotNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
