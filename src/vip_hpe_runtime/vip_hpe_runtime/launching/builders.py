from __future__ import annotations

from typing import Any

from launch.actions import LogInfo
from launch_ros.actions import Node


def _session_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    return cfg.get("session", {})


def _topics_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    return cfg.get("topics", {})


def _common_node_params(cfg: dict[str, Any]) -> dict[str, Any]:
    session = _session_cfg(cfg)

    return {
        "use_sim_time": bool(session.get("use_sim_time", False)),
    }


def _node_log_level(cfg: dict[str, Any]) -> str:
    return str(_session_cfg(cfg).get("log_level", "info"))


def _node(
    *,
    package: str,
    executable: str,
    name: str,
    parameters: dict[str, Any],
    cfg: dict[str, Any],
) -> Node:
    merged_params = {}
    merged_params.update(_common_node_params(cfg))
    merged_params.update(parameters)

    return Node(
        package=package,
        executable=executable,
        name=name,
        output="screen",
        emulate_tty=True,
        parameters=[merged_params],
        arguments=["--ros-args", "--log-level", _node_log_level(cfg)],
    )


def build_radar_replay_node(cfg: dict[str, Any]) -> Node:
    radar_cfg = cfg["sources"]["radar"]
    topics = _topics_cfg(cfg)

    params = dict(radar_cfg.get("params", {}))
    params.update(
        {
            "output_topic": topics.get("radar_points", "/radar/points"),
            "status_topic": topics.get("debug_status", "/debug/replay_status"),
        }
    )

    return _node(
        package="vip_hpe_runtime",
        executable="radar_replay_node",
        name="radar_replay_node",
        parameters=params,
        cfg=cfg,
    )


def build_pose_gt_replay_node(cfg: dict[str, Any]) -> Node:
    pose_cfg = cfg["pose"]
    topics = _topics_cfg(cfg)

    params = dict(pose_cfg.get("params", {}))
    params.update(
        {
            "output_topic": topics.get("pose_people", "/pose/people"),
            "status_topic": topics.get("debug_status", "/debug/replay_status"),
        }
    )

    return _node(
        package="vip_hpe_runtime",
        executable="pose_gt_replay_node",
        name="pose_gt_replay_node",
        parameters=params,
        cfg=cfg,
    )

def build_pose_gt_replay_synced_node(cfg: dict[str, Any]) -> Node:
    """
    Build an inference-like GT pose emulator.

    This node subscribes to radar frames, runs the configured point-cloud
    preprocessor, then publishes the matching GT pose from the replay pickle.
    """
    pose_cfg = cfg["pose"]
    topics = _topics_cfg(cfg)
    preprocessing_cfg = cfg.get("preprocessing", {})

    params = dict(pose_cfg.get("params", {}))

    preprocessor_config_path = preprocessing_cfg.get("preprocessor_config_path", "")
    if not preprocessor_config_path:
        raise ValueError(
            "pose.kind='replay_gt_synced' requires "
            "preprocessing.preprocessor_config_path"
        )

    params.update(
        {
            "input_topic": topics.get("radar_points", "/radar/points"),
            "output_topic": topics.get("pose_people", "/pose/people"),
            "status_topic": topics.get("debug_status", "/debug/replay_status"),
            "preprocessor_config_path": preprocessor_config_path,
        }
    )

    return _node(
        package="vip_hpe_runtime",
        executable="pose_gt_inference_emulator_node",
        name="pose_gt_inference_emulator_node",
        parameters=params,
        cfg=cfg,
    )


def build_matplotlib_visualizer_node(cfg: dict[str, Any]) -> Node:
    visualizer_cfg = cfg["sinks"]["visualizer"]
    topics = _topics_cfg(cfg)

    params = dict(visualizer_cfg.get("params", {}))
    params.update(
        {
            "radar_topic": topics.get("radar_points", "/radar/points"),
            "pose_topic": topics.get("pose_people", "/pose/people"),
            "camera_topic": topics.get("camera_frames", "/camera/image"),
        }
    )

    return _node(
        package="vip_hpe_runtime",
        executable="animated_plot_node",
        name="animated_plot_node",
        parameters=params,
        cfg=cfg,
    )


RADAR_BUILDERS = {
    "replay": build_radar_replay_node,
}

POSE_BUILDERS = {
    "replay_gt": build_pose_gt_replay_node, # Pose node independently replays saved pose frames from pickle. Useful when you want to visualize saved poses without requiring radar input.
    "replay_gt_synced": build_pose_gt_replay_synced_node, #Best current demonstration of the future model inference pipeline.
}

VISUALIZER_BUILDERS = {
    "matplotlib_3d": build_matplotlib_visualizer_node,
}


def build_session_actions(cfg: dict[str, Any]) -> list[Any]:
    """
    Convert a validated session config into launch actions.
    """
    actions: list[Any] = []

    session_name = cfg.get("session", {}).get("name", "unnamed_session")
    actions.append(LogInfo(msg=f"Launching VIP HPE session: {session_name}"))

    radar_cfg = cfg.get("sources", {}).get("radar", {})
    if radar_cfg.get("enabled", False):
        kind = radar_cfg["kind"]
        actions.append(RADAR_BUILDERS[kind](cfg))

    pose_cfg = cfg.get("pose", {})
    if pose_cfg.get("enabled", False):
        kind = pose_cfg["kind"]
        actions.append(POSE_BUILDERS[kind](cfg))

    visualizer_cfg = cfg.get("sinks", {}).get("visualizer", {})
    if visualizer_cfg.get("enabled", False):
        kind = visualizer_cfg["kind"]
        actions.append(VISUALIZER_BUILDERS[kind](cfg))

    return actions