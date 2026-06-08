from __future__ import annotations

from pathlib import Path
from typing import Any


class SessionConfigError(ValueError):
    """Raised when a runtime session config is invalid."""


def _require_mapping(cfg: dict[str, Any], key: str) -> dict[str, Any]:
    value = cfg.get(key)
    if not isinstance(value, dict):
        raise SessionConfigError(f"'{key}' must exist and must be a mapping/dictionary")
    return value


def _require_key(mapping: dict[str, Any], key: str, context: str) -> Any:
    if key not in mapping:
        raise SessionConfigError(f"Missing required key '{context}.{key}'")
    return mapping[key]


def _require_existing_file(path_value: str, context: str) -> None:
    if not path_value:
        raise SessionConfigError(f"'{context}' must not be empty")

    path = Path(path_value)
    if not path.exists():
        raise SessionConfigError(f"'{context}' does not exist: {path}")


def validate_session_config(cfg: dict[str, Any]) -> None:
    """
    Validate session config before launch actions are created.

    Keep this strict enough to catch broken developer configs early, but not so
    strict that it prevents future modes from being added.
    """
    session_cfg = _require_mapping(cfg, "session")
    topics_cfg = _require_mapping(cfg, "topics")
    sources_cfg = _require_mapping(cfg, "sources")
    pose_cfg = _require_mapping(cfg, "pose")
    sinks_cfg = _require_mapping(cfg, "sinks")

    _require_key(session_cfg, "name", "session")
    _require_key(topics_cfg, "radar_points", "topics")
    _require_key(topics_cfg, "pose_people", "topics")

    radar_cfg = sources_cfg.get("radar", {})
    if radar_cfg is None:
        radar_cfg = {}
    if not isinstance(radar_cfg, dict):
        raise SessionConfigError("'sources.radar' must be a mapping/dictionary")

    radar_enabled = bool(radar_cfg.get("enabled", False))
    radar_kind = radar_cfg.get("kind", "none")

    if radar_enabled:
        if radar_kind not in {"replay"}:
            raise SessionConfigError(
                f"Unsupported sources.radar.kind='{radar_kind}'. "
                "Currently supported: replay"
            )

        radar_params = radar_cfg.get("params", {})
        if not isinstance(radar_params, dict):
            raise SessionConfigError("'sources.radar.params' must be a mapping/dictionary")

        if radar_kind == "replay":
            _require_existing_file(
                str(radar_params.get("pickle_path", "")),
                "sources.radar.params.pickle_path",
            )

    camera_cfg = sources_cfg.get("camera", {})
    if camera_cfg is None:
        camera_cfg = {}
    if not isinstance(camera_cfg, dict):
        raise SessionConfigError("'sources.camera' must be a mapping/dictionary")

    camera_enabled = bool(camera_cfg.get("enabled", False))
    if camera_enabled:
        raise SessionConfigError(
            "Camera sources are not implemented yet. Set sources.camera.enabled: false"
        )

    pose_enabled = bool(pose_cfg.get("enabled", False))
    pose_kind = pose_cfg.get("kind", "none")

    if pose_enabled:
        if pose_kind not in {"replay_gt", "replay_gt_synced"}:
            raise SessionConfigError(
                f"Unsupported pose.kind='{pose_kind}'. "
                "Currently supported: replay_gt"
            )

        pose_params = pose_cfg.get("params", {})
        if not isinstance(pose_params, dict):
            raise SessionConfigError("'pose.params' must be a mapping/dictionary")

        if pose_kind in {"replay_gt", "replay_gt_synced"}:
            _require_existing_file(
                str(pose_params.get("pickle_path", "")),
                "pose.params.pickle_path",
            )

        if pose_kind == "replay_gt_synced":
            if not radar_enabled:
                raise SessionConfigError(
                    "pose.kind='replay_gt_synced' requires sources.radar.enabled: true"
                )

            preprocessing_cfg = cfg.get("preprocessing", {})
            if not isinstance(preprocessing_cfg, dict):
                raise SessionConfigError("'preprocessing' must be a mapping/dictionary")

            _require_existing_file(
                str(preprocessing_cfg.get("preprocessor_config_path", "")),
                "preprocessing.preprocessor_config_path",
            )

    visualizer_cfg = sinks_cfg.get("visualizer", {})
    if visualizer_cfg is None:
        visualizer_cfg = {}
    if not isinstance(visualizer_cfg, dict):
        raise SessionConfigError("'sinks.visualizer' must be a mapping/dictionary")

    visualizer_enabled = bool(visualizer_cfg.get("enabled", False))
    visualizer_kind = visualizer_cfg.get("kind", "none")

    if visualizer_enabled:
        if visualizer_kind not in {"matplotlib_3d"}:
            raise SessionConfigError(
                f"Unsupported sinks.visualizer.kind='{visualizer_kind}'. "
                "Currently supported: matplotlib_3d"
            )

        if not radar_enabled and not pose_enabled:
            raise SessionConfigError(
                "sinks.visualizer.enabled is true, but both radar and pose are disabled"
            )

    recorder_cfg = sinks_cfg.get("recorder", {})
    if recorder_cfg is None:
        recorder_cfg = {}
    if not isinstance(recorder_cfg, dict):
        raise SessionConfigError("'sinks.recorder' must be a mapping/dictionary")

    recorder_enabled = bool(recorder_cfg.get("enabled", False))
    if recorder_enabled:
        raise SessionConfigError(
            "Recorder sink is not implemented yet. Set sinks.recorder.enabled: false"
        )