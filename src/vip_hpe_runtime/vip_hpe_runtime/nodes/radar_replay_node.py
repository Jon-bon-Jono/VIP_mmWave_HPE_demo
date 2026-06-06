"""Simulated radar driver node.

This node replays point cloud frames from a pickle file and publishes them as
`vip_hpe_msgs/msg/RadarFrame`. Later, a live TI radar UART/LVDS driver should
publish the same message type on the same topic.
"""

from __future__ import annotations

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from vip_hpe_msgs.msg import RadarFrame
from vip_hpe_runtime.adapters.ros_conversions import frame_to_radar_msg
from vip_hpe_runtime.nodes.replay_base import ReplayCursor, load_replay_or_raise


class RadarReplayNode(Node):
    def __init__(self):
        super().__init__('radar_replay_node')
        self.declare_parameter('pickle_path', 'C:/Users/GSBME/SmartCupStudy/Unified_network/data_sets/UNSW-PANOPTES/UNSW-PANOPTES-ETL-Pipeline/data/prepared/pc_raw_hpe_act/07_SW.pickle')
        self.declare_parameter('radar_topic', '/radar/points')
        self.declare_parameter('status_topic', '/debug/replay_status')
        self.declare_parameter('frame_id', 'radar_link')
        self.declare_parameter('start_index', 0)
        self.declare_parameter('end_index', -1)
        self.declare_parameter('playback_hz', 10.0)
        self.declare_parameter('loop', False)
        self.declare_parameter('gtrack_filtering', True)
        self.declare_parameter('fps_fallback', 10.0)

        self.get_logger().info("DEBUG: RadarReplayNode __init__ is running")

        print("PRINNT DEBUG: RadarReplayNode __init__ is running", flush=True)
        self.frame_id = self.get_parameter('frame_id').get_parameter_value().string_value
        pickle_path = self.get_parameter('pickle_path').get_parameter_value().string_value
        topic = self.get_parameter('radar_topic').get_parameter_value().string_value
        status_topic = self.get_parameter('status_topic').get_parameter_value().string_value
        playback_hz = self.get_parameter('playback_hz').get_parameter_value().double_value
        start_index = self.get_parameter('start_index').get_parameter_value().integer_value
        end_index = self.get_parameter('end_index').get_parameter_value().integer_value
        loop = self.get_parameter('loop').get_parameter_value().bool_value
        gtrack_filtering = self.get_parameter('gtrack_filtering').get_parameter_value().bool_value
        fps_fallback = self.get_parameter('fps_fallback').get_parameter_value().double_value

        self.publisher = self.create_publisher(RadarFrame, topic, 10)
        self.status_pub = self.create_publisher(String, status_topic, 10)

        self.replay = load_replay_or_raise(pickle_path, gtrack_filtering, fps_fallback)
        self.cursor = ReplayCursor(self.replay, start_index, end_index, loop)

        period = 1.0 / max(float(playback_hz), 1e-6)
        self.timer = self.create_timer(period, self._on_timer)
        self.get_logger().info(
            f'Radar replay loaded {len(self.replay)} frames from {pickle_path}. '
            f'Publishing {topic} at {playback_hz:.3f} Hz.'
        )

    def _on_timer(self):
        frame = self.cursor.next_frame()
        if frame is None:
            self.get_logger().info('Radar replay reached end of requested range. Shutting down timer.')
            self.timer.cancel()
            return
        self.publisher.publish(frame_to_radar_msg(frame, self, self.frame_id))
        status = String()
        status.data = f'radar_replay frame_index={frame.frame_index} n_points={frame.pc.shape[0]}'
        self.status_pub.publish(status)


def main(args=None):
    rclpy.init(args=args)
    node = RadarReplayNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
