import numpy as np

from vip_hpe_runtime.replay.living_lab import pose_3d_to_radar_plot_frame


def test_pose_3d_to_radar_plot_frame_preserves_confidence_and_scales():
    pose = np.array([[[1000.0, 2000.0, 3000.0, 0.5]]], dtype=np.float32)
    out = pose_3d_to_radar_plot_frame(pose)
    assert out.shape == (1, 1, 4)
    assert np.allclose(out[0, 0], [1.0, 3.0, -2.0, 0.5])
