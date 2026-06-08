from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

from vip_hpe_runtime.launching.config import load_session_config
from vip_hpe_runtime.launching.validation import validate_session_config
from vip_hpe_runtime.launching.builders import build_session_actions


def _launch_setup(context, *args, **kwargs):
    session_config_path = LaunchConfiguration("session_config").perform(context)

    cfg = load_session_config(session_config_path)
    validate_session_config(cfg)

    return build_session_actions(cfg)


def generate_launch_description():
    default_session_config = PathJoinSubstitution(
        [
            FindPackageShare("vip_hpe_runtime"),
            "config",
            "sessions",
            "replay_pc_gt_pose_visualize.yaml",
        ]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "session_config",
                default_value=default_session_config,
                description="Path to YAML file describing the runtime session.",
            ),
            OpaqueFunction(function=_launch_setup),
        ]
    )