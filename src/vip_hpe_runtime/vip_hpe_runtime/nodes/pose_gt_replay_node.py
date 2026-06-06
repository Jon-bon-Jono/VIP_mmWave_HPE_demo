"""Simulated inference node.

This node reads the same pickle stream but publishes the stored pose ground truth
as if it came from a deployed pose-estimation model. Later, the live model node
should publish the same `PersonPose3DArray` message.
"""

from __future__ import annotations

import rclpy
from rclpy.node import Node

from vip_hpe_msgs.msg import PersonPose3DArray
from vip_hpe_runtime.adapters.ros_conversions import frame_to_pose_msg
from vip_hpe_runtime.nodes.replay_base import ReplayCursor, load_replay_or_raise


class PoseGtReplayNode(Node):
    def __init__(self):
        super().__init__('pose_gt_replay_node')
        self.declare_parameter('pickle_path', '')
        self.declare_parameter('pose_topic', '/pose/people')
        self.declare_parameter('frame_id', 'radar_link')
        self.declare_parameter('start_index', 0)
        self.declare_parameter('end_index', -1)
        self.declare_parameter('playback_hz', 10.0)
        self.declare_parameter('loop', False)
        self.declare_parameter('gtrack_filtering', True)
        self.declare_parameter('fps_fallback', 10.0)

        self.frame_id = self.get_parameter('frame_id').get_parameter_value().string_value
        pickle_path = self.get_parameter('pickle_path').get_parameter_value().string_value
        topic = self.get_parameter('pose_topic').get_parameter_value().string_value
        playback_hz = self.get_parameter('playback_hz').get_parameter_value().double_value
        start_index = self.get_parameter('start_index').get_parameter_value().integer_value
        end_index = self.get_parameter('end_index').get_parameter_value().integer_value
        loop = self.get_parameter('loop').get_parameter_value().bool_value
        gtrack_filtering = self.get_parameter('gtrack_filtering').get_parameter_value().bool_value
        fps_fallback = self.get_parameter('fps_fallback').get_parameter_value().double_value

        self.publisher = self.create_publisher(PersonPose3DArray, topic, 10)
        self.replay = load_replay_or_raise(pickle_path, gtrack_filtering, fps_fallback)
        self.cursor = ReplayCursor(self.replay, start_index, end_index, loop)

        period = 1.0 / max(float(playback_hz), 1e-6)
        self.timer = self.create_timer(period, self._on_timer)
        self.get_logger().info(
            f'Pose GT replay loaded {len(self.replay)} frames from {pickle_path}. '
            f'Publishing {topic} at {playback_hz:.3f} Hz.'
        )

    def _on_timer(self):
        frame = self.cursor.next_frame()
        if frame is None:
            self.get_logger().info('Pose replay reached end of requested range. Shutting down timer.')
            self.timer.cancel()
            return
        self.publisher.publish(frame_to_pose_msg(frame, self, self.frame_id))


def main(args=None):
    rclpy.init(args=args)
    node = PoseGtReplayNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
