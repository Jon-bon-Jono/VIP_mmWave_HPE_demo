"""Placeholder for the future deployed model inference node.

The point of this stub is architectural: it subscribes to the same radar topic
that the replay visualiser uses and will eventually publish the same pose topic
as `pose_gt_replay_node`.
"""

from __future__ import annotations

import rclpy
from rclpy.node import Node

from vip_hpe_msgs.msg import RadarFrame, PersonPose3DArray
from vip_hpe_runtime.adapters.ros_conversions import radar_msg_to_numpy, pose_msg_to_numpy
from vip_hpe_core.preprocessing.model_input import PointCloudPreprocessor

class LiveModelInferenceNode(Node):
    def __init__(self):
        super().__init__('live_model_inference_node')
        self.declare_parameter('radar_topic', '/radar/points')
        self.declare_parameter('pose_topic', '/pose/people')
        self.declare_parameter('model_path', '')
        self.declare_parameter('frame_id', 'radar_link')

        radar_topic = self.get_parameter('radar_topic').get_parameter_value().string_value
        pose_topic = self.get_parameter('pose_topic').get_parameter_value().string_value
        self.frame_id = self.get_parameter('frame_id').get_parameter_value().string_value

        self.preprocessor = PointCloudPreprocessor(config={})

        self.publisher = self.create_publisher(PersonPose3DArray, pose_topic, 10)
        self.subscription = self.create_subscription(RadarFrame, radar_topic, self._on_radar_frame, 10)
        self.get_logger().warn(
            'LiveModelInferenceNode is a placeholder. It republishes empty pose arrays. '
            'Replace _run_model() with ONNX/PyTorch inference later.'
        )

    def _on_radar_frame(self, radar_msg: RadarFrame):
        pose_msg = self._run_model(radar_msg)
        self.publisher.publish(pose_msg)

    def _run_model(self, radar_msg: RadarFrame) -> PersonPose3DArray:
        points_np = radar_msg_to_numpy(radar_msg)
        model_input_np = self.preprocessor.transform(points_np)

        # TODO: run deployed model,
        # decode skeletons, and populate PersonPose3DArray.
        msg = PersonPose3DArray()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id
        msg.frame_index = radar_msg.frame_index
        msg.source_timestamp = radar_msg.source_timestamp
        msg.people = []
        return msg


def main(args=None):
    rclpy.init(args=args)
    node = LiveModelInferenceNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
