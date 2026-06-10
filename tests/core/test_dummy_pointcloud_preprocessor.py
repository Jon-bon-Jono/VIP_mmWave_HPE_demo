import numpy as np
import pytest

from vip_hpe_core.preprocessing.model_input import DummyPointCloudPreprocessor
from vip_hpe_core.preprocessing.registry import build_preprocessor


def test_dummy_preprocessor_casts_to_float32_and_preserves_values():
    points = np.array(
        [
            [1.0, 2.0, 3.0, 0.1, 10.0, 4.0],
            [4.0, 5.0, 6.0, 0.2, 11.0, 5.0],
        ],
        dtype=np.float64,
    )

    preprocessor = DummyPointCloudPreprocessor(
        {
            "expected_num_features": 6,
            "copy": True,
        }
    )

    out = preprocessor.transform(points, frame_metadata={"frame_index": 123})

    assert out.array.dtype == np.float32
    assert out.array.shape == (2, 6)
    assert np.allclose(out.array, points.astype(np.float32))

    assert out.metadata["frame_index"] == 123
    assert out.metadata["preprocessor_name"] == "dummy_pointcloud"
    assert out.metadata["preprocessor_version"] == "0.1.0"
    assert out.metadata["num_points"] == 2
    assert out.metadata["num_features"] == 6


def test_dummy_preprocessor_rejects_wrong_feature_count():
    points = np.zeros((2, 5), dtype=np.float32)

    preprocessor = DummyPointCloudPreprocessor(
        {
            "expected_num_features": 6,
        }
    )

    with pytest.raises(ValueError, match="Expected 6 point features"):
        preprocessor.transform(points)


def test_dummy_preprocessor_rejects_non_2d_input():
    points = np.zeros((2, 3, 4), dtype=np.float32)

    preprocessor = DummyPointCloudPreprocessor()

    with pytest.raises(ValueError, match="must have shape"):
        preprocessor.transform(points)


def test_build_preprocessor_factory_creates_dummy_preprocessor():
    preprocessor = build_preprocessor(
        {
            "name": "dummy_pointcloud",
            "params": {
                "expected_num_features": 6,
            },
        }
    )

    assert isinstance(preprocessor, DummyPointCloudPreprocessor)
    assert preprocessor.output_spec.name == "dummy_pointcloud"