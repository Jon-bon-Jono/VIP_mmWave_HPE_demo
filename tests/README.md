tests/core
  Must not require ROS.
  Must not require PyTorch.
  Should pass in both ROS and ML environments.

tests/runtime
  May require ROS setup and generated messages.
  Runs in vip_ros2_jazzy_dev.

tests/ml
  May require PyTorch.
  Runs in vip_hpe_ml_dev.