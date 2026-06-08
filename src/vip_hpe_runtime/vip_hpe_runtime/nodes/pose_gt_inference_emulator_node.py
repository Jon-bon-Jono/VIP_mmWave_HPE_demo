from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import rclpy
import yaml
from rclpy.node import Node
from std_msgs.msg import String

from vip_hpe_msgs.msg import Joint3D, PersonPose3D, PersonPose3DArray, RadarFrame

from vip_hpe_core.preprocessing.registry import build_preprocessor
from vip_hpe_core.preprocessing.config import build_preprocessor_from_yaml
from vip_hpe_core.constants.kinect import KINECT_JOINT_NAMES

from vip_hpe_runtime.nodes.replay_base import load_replay_or_raise
from vip_hpe_runtime.adapters.ros_conversions import radar_msg_to_numpy, pose_array_from_replay_frame

class PoseGtInferenceEmulatorNode(Node):
    """
    Inference-like GT pose emulator.

    This node behaves like the future live model inference node:

        RadarFrame subscription
          -> RadarFrame to NumPy
          -> PointCloudPreprocessor.transform(...)
          -> pose output

    But instead of running a deployed pose model, it looks up the matching GT
    pose from the replay pickle using RadarFrame.frame_index.

    This demonstrates the runtime preprocessing path without introducing
    an actual HPE model PyTorch or ONNX Runtime.
    """

    def __init__(self):
        super().__init__("pose_gt_inference_emulator_node")

        self.declare_parameter("pickle_path", "")
        self.declare_parameter("input_topic", "/radar/points")
        self.declare_parameter("output_topic", "/pose/people")
        self.declare_parameter("status_topic", "/debug/replay_status")
        self.declare_parameter("preprocessor_config_path", "")
        self.declare_parameter("require_preprocessing_success", True)
        self.declare_parameter("debug_log_every_n", 30)

        self.pickle_path = Path(str(self.get_parameter("pickle_path").value))
        self.input_topic = str(self.get_parameter("input_topic").value)
        self.output_topic = str(self.get_parameter("output_topic").value)
        self.status_topic = str(self.get_parameter("status_topic").value)
        self.preprocessor_config_path = Path(
            str(self.get_parameter("preprocessor_config_path").value)
        )
        self.require_preprocessing_success = bool(
            self.get_parameter("require_preprocessing_success").value
        )
        self.debug_log_every_n = int(self.get_parameter("debug_log_every_n").value)

        if not self.pickle_path.exists():
            raise FileNotFoundError(f"Replay pickle does not exist: {self.pickle_path}")

        if not self.preprocessor_config_path.exists():
            raise FileNotFoundError(
                f"Preprocessor config does not exist: {self.preprocessor_config_path}"
            )

        self.replay = load_replay_or_raise(self.pickle_path)
        self.get_logger().info(f"DEBUG: PoseGtInferenceEmulatorNode.preprocessor_config_path: {self.preprocessor_config_path}")
        self.preprocessor = build_preprocessor_from_yaml(self.preprocessor_config_path)

        self.pose_pub = self.create_publisher(PersonPose3DArray, self.output_topic, 10)
        self.status_pub = self.create_publisher(String, self.status_topic, 10)

        self.radar_sub = self.create_subscription(RadarFrame,self.input_topic,self.on_radar_frame,10)

        self.num_received = 0
        self.num_published = 0
        self.num_preprocess_errors = 0
        self.num_lookup_errors = 0

        spec = self.preprocessor.output_spec

        self.get_logger().info(
            "PoseGtInferenceEmulatorNode ready. "
            f"input_topic={self.input_topic}, "
            f"output_topic={self.output_topic}, "
            f"pickle_path={self.pickle_path}, "
            f"preprocessor={spec.name}:{spec.version}, "
            f"preprocessor_config={self.preprocessor_config_path}"
        )

    def on_radar_frame(self, msg: RadarFrame) -> None:
        self.num_received += 1

        frame_index = int(msg.frame_index)
        points_np = radar_msg_to_numpy(msg)

        try:
            preprocessed = self.preprocessor.transform(
                points_np,
                frame_metadata={
                    "frame_index": frame_index,
                    "stamp_sec": int(msg.header.stamp.sec),
                    "stamp_nanosec": int(msg.header.stamp.nanosec),
                    "input_topic": self.input_topic,
                },
            )
        except Exception as exc:
            self.num_preprocess_errors += 1
            self.get_logger().error(
                f"Preprocessing failed for frame_index={frame_index}: {exc}"
            )

            if self.require_preprocessing_success:
                return

            preprocessed = None

        try:
            replay_frame = self.replay[frame_index]
            pose_msg = pose_array_from_replay_frame(
                replay_frame,
                radar_msg=msg,
            )
        except Exception as exc:
            self.num_lookup_errors += 1
            self.get_logger().error(
                f"GT pose lookup failed for frame_index={frame_index}: {exc}"
            )
            return

        self.pose_pub.publish(pose_msg)
        self.num_published += 1

        if self.debug_log_every_n > 0:
            if self.num_received == 1 or self.num_received % self.debug_log_every_n == 0:
                if preprocessed is not None:
                    prep_shape = tuple(preprocessed.array.shape)
                    prep_dtype = str(preprocessed.array.dtype)
                else:
                    prep_shape = None
                    prep_dtype = None

                status = (
                    f"pose_gt_inference_emulator "
                    f"frame_index={frame_index} "
                    f"points={points_np.shape[0]} "
                    f"preprocessed_shape={prep_shape} "
                    f"preprocessed_dtype={prep_dtype} "
                    f"people={len(pose_msg.people)} "
                    f"received={self.num_received} "
                    f"published={self.num_published}"
                )

                self.get_logger().info(status)
                self.status_pub.publish(String(data=status))


def main(args=None):
    rclpy.init(args=args)

    node = PoseGtInferenceEmulatorNode()

    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()