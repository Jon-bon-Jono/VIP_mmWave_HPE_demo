# VIP mmWave HPE Demo

This repository is a Windows-friendly ROS 2 Jazzy + RoboStack runtime skeleton for mmWave-radar-based human pose estimation. The current system replays prerecorded mmWave point-cloud frames and Kinect-derived 3D pose ground truth from pickle files, visualises the result, and demonstrates the preprocessing/inference pathway that will later be used by deployed pose-estimation models.

The current default session is configured by:

```text
src/vip_hpe_runtime/config/sessions/replay_pc_gt_pose_visualize.yaml
```

and launched with:

```cmd
ros2 launch vip_hpe_runtime session.launch.py
```

The default session starts three nodes:

```text
radar_replay_node
  Reads prerecorded point-cloud frames from data/ll_replay/07_SW.pickle.
  Publishes vip_hpe_msgs/msg/RadarFrame on /radar/points.

pose_gt_inference_emulator_node
  Subscribes to /radar/points.
  Converts each RadarFrame to a NumPy point-cloud array.
  Builds a vip_hpe_core PointCloudPreprocessor from YAML.
  Runs preprocessing.
  Looks up the matching GT pose using RadarFrame.frame_index.
  Publishes vip_hpe_msgs/msg/PersonPose3DArray on /pose/people.

animated_plot_node
  Subscribes to /radar/points and /pose/people.
  Displays an animated Matplotlib 3D point-cloud and skeleton plot.
```

The system deliberately uses the same ROS topics that future live nodes should use:

```text
/radar/points          vip_hpe_msgs/msg/RadarFrame
/pose/people           vip_hpe_msgs/msg/PersonPose3DArray
/debug/replay_status   std_msgs/msg/String
```

## Repository structure

```text
VIP_MMWAVE_HPE_DEMO/
  src/
    vip_hpe_core/       Shared ROS-free, PyTorch-free preprocessing utilities.
    vip_hpe_msgs/       Custom ROS 2 message definitions.
    vip_hpe_runtime/    ROS 2 nodes, launch files, session config, adapters, visualisation.

  ml/                   Placeholder for the future PyTorch training framework.
                        Contains COLCON_IGNORE so colcon ignores it.

  tests/
    core/               Tests for vip_hpe_core. Should not require ROS or PyTorch.
    runtime/            Tests for vip_hpe_runtime logic. May require the ROS environment.
    ml/                 Placeholder for future tests which may require PyTorch.

  docs/
    ros2_dev_notes.md   Longer explanation of ROS 2 concepts used in this project.

  data/                 Local replay data. Ignored by Git.
```

The most important design boundary is:

```text
vip_hpe_core
  Shared processing and constants between runtime (Group 1) and machine learning (Group 2).
  Must not import ROS, rclpy, vip_hpe_msgs, PyTorch, Ultralytics, ONNX Runtime, or Matplotlib.

vip_hpe_runtime
  ROS-specific runtime package.
  May import vip_hpe_core and vip_hpe_msgs.

ml/
  Future PyTorch training framework.
  Should import vip_hpe_core for shared preprocessing.
```

## Windows 11 ROS 2 setup

These instructions assume Windows 11, Conda, and the provided RoboStack-based ROS 2 Jazzy environment file.

### 1. Create the Conda environment

Open **Command Prompt** or **Anaconda Prompt** in the repository root:

```cmd
cd C:\path\to\VIP_MMWAVE_HPE_DEMO
```

Create the Conda environment:

```cmd
conda env create -f vip_ros2_jazzy_dev.yml
```

Activate it:

```cmd
conda activate vip_ros2_jazzy_dev
```

This makes `python`, `ros2`, `colcon`, and the RoboStack ROS 2 packages available in the current terminal.

### 2. Build the ROS 2 workspace

For the first build, use an Administrator terminal if Windows blocks symbolic-link creation. Alternatively, enable Windows Developer Mode.

From the repository root:

```cmd
colcon build --merge-install --symlink-install
```

`colcon` builds the ROS 2 packages in `src/`.

`--merge-install` keeps the Windows install layout simpler.

`--symlink-install` makes development faster because many installed files point back to the source/build tree instead of being copied into the install space. With the `PYTHONPATH` override below, normal edits to Python files usually only require restarting the node/launch, not rebuilding.

### 3. Set up each new terminal

Every new terminal needs the environment activated and the built workspace loaded:

```cmd
conda activate vip_ros2_jazzy_dev
cd C:\path\to\VIP_MMWAVE_HPE_DEMO
install\setup.bat
set PYTHONPATH=%CD%\src\vip_hpe_core;%CD%\src\vip_hpe_runtime;%PYTHONPATH%
```

The `install\setup.bat` command lets ROS 2 find local packages such as `vip_hpe_core`, `vip_hpe_msgs`, and `vip_hpe_runtime`.

The `PYTHONPATH` command forces Python to import the live source versions of `vip_hpe_core` and `vip_hpe_runtime` before installed/build copies.

You can verify this with:

```cmd
python -c "import vip_hpe_runtime.nodes.radar_replay_node as m; print(m.__file__)"
python -c "import vip_hpe_core.preprocessing.model_input as m; print(m.__file__)"
```

Both paths should point inside `src\...`, not only inside `build\...` or `install\...`.

## Replay data

The default session supports replaying pre-recorded data (UNSW's 'Living Lab' dataset) from this file:

```text
data/ll_replay/07_SW.pickle
```

The `data/` folder is local-only and should not be committed to Git. Download or copy [the sample pickle file](https://unsw-my.sharepoint.com/:u:/g/personal/z5162987_ad_unsw_edu_au/IQANKS8mCXM5T6kvvYKfvwbzAfD1-4XdXFwztphrZN7kapY?e=ZIZGL2) into:

```text
VIP_MMWAVE_HPE_DEMO/data/ll_replay/07_SW.pickle
```

## Run the default session

From a terminal that has completed the setup steps above:

```cmd
ros2 launch vip_hpe_runtime session.launch.py
```

This uses the packaged default session config:

```text
src/vip_hpe_runtime/config/sessions/replay_pc_gt_pose_visualize.yaml
```

You can also pass the config explicitly:

```cmd
ros2 launch vip_hpe_runtime session.launch.py session_config:="src\vip_hpe_runtime\config\sessions\replay_pc_gt_pose_visualize.yaml"
```

Run the command from the repository root. The current session config uses:

```yaml
session:
  workspace_root: "."
```

so relative paths such as `data/ll_replay/07_SW.pickle` and `src/vip_hpe_core/config/preprocessing/dummy_pointcloud.yaml` are resolved relative to the current working directory.

A Matplotlib 3D animation window should open. The visualiser subscribes to ROS topics; it does not read the pickle file directly.

## Session configuration

Runtime sessions are configured with YAML files under:

```text
src/vip_hpe_runtime/config/sessions/
```

The default session file is:

```text
src/vip_hpe_runtime/config/sessions/replay_pc_gt_pose_visualize.yaml
```

It describes:

```text
session       Session name, workspace root, sim-time setting, log level.
topics        Topic names such as /radar/points and /pose/people.
sources       Data sources such as radar replay.
pose          Pose source/inference mode.
preprocessing Path to the point-cloud preprocessor YAML.
sinks         Output actions such as visualisation or recording.
```

The current default pose mode is:

```yaml
pose:
  enabled: true
  kind: replay_gt_synced
```

`replay_gt_synced` is an inference-emulator mode. It waits for incoming radar frames, preprocesses the radar point cloud, then publishes the matching ground-truth pose from the pickle file. This is currently the best demonstration of the future live model-inference pathway without requiring a deployed model.

The currently available pose modes are:

```text
replay_gt
  Independently replays saved pose frames from the pickle file.
  Useful when pose replay should not depend on incoming radar messages.

replay_gt_synced
  Subscribes to /radar/points and publishes the matching GT pose for each incoming RadarFrame.
  Demonstrates the future inference-node pattern.
```

## Preprocessor configuration

The default session points to this preprocessor YAML:

```text
src/vip_hpe_core/config/preprocessing/dummy_pointcloud.yaml
```

Current contents:

```yaml
name: dummy_pointcloud
params:
  expected_num_features: 6
  copy: true
```

This builds `DummyPointCloudPreprocessor` from `vip_hpe_core`. The dummy preprocessor verifies that the incoming point-cloud array has six columns and returns a `float32` NumPy array plus metadata. It exists to demonstrate the shared preprocessing interface before a real model-specific preprocessor is implemented.

Future real preprocessors should live in `vip_hpe_core` and should remain NumPy-only. PyTorch conversion should happen in `ml/`, not in `vip_hpe_core`.

## Run individual nodes

The recommended way to run the full system is:

```cmd
ros2 launch vip_hpe_runtime session.launch.py
```

For debugging, you can run one packaged node with `ros2 run`.

Radar replay node:

```cmd
ros2 run vip_hpe_runtime radar_replay_node --ros-args ^
  -p pickle_path:="data/ll_replay/07_SW.pickle" ^
  -p start_index:=35000 ^
  -p playback_hz:=10.0 ^
  -p loop:=true
```

Pose GT inference emulator:

```cmd
ros2 run vip_hpe_runtime pose_gt_inference_emulator_node --ros-args ^
  -p pickle_path:="data/ll_replay/07_SW.pickle" ^
  -p input_topic:=/radar/points ^
  -p output_topic:=/pose/people ^
  -p preprocessor_config_path:="src/vip_hpe_core/config/preprocessing/dummy_pointcloud.yaml"
```

Animated plot node:

```cmd
ros2 run vip_hpe_runtime animated_plot_node --ros-args ^
  -p radar_topic:=/radar/points ^
  -p pose_topic:=/pose/people
```

You can also run Python files directly for quick debugging, for example:

```cmd
python src\vip_hpe_runtime\vip_hpe_runtime\nodes\radar_replay_node.py
```

That is useful for component-level debugging only. It bypasses ROS package discovery, installed entry points, launch files, and session config. Use `ros2 launch` to test the actual system.

## When to rebuild

You must rebuild if you modify:

```text
src/vip_hpe_msgs/msg/*.msg
src/vip_hpe_msgs/CMakeLists.txt
src/vip_hpe_msgs/package.xml
src/vip_hpe_core/setup.py
src/vip_hpe_core/package.xml
src/vip_hpe_runtime/setup.py
src/vip_hpe_runtime/package.xml
```

You must also rebuild if you:

```text
add a new ROS package under src/ (current ROS packages under src/ are vip_hpe_core, vip_hpe_runtime, ...)
add a new ROS executable node and register it in setup.py entry_points
rename an executable
change setup.py data_files or installed resource layout
change dependencies in package.xml or the Conda environment file
```

You usually do **not** need to rebuild for normal edits to existing Python files under:

```text
src/vip_hpe_core/vip_hpe_core/
src/vip_hpe_runtime/vip_hpe_runtime/
```

Just stop and restart the node/launch command.

You usually do **not** need to rebuild when adding helper Python modules that are imported by existing nodes, as long as the files live under the Python package and the `PYTHONPATH` source override is active.

With `--symlink-install`, edits to existing launch files and existing YAML config files are usually picked up after restarting the launch. Rebuild when adding new installed resources or changing how resources are installed.

After pulling from GitHub, rebuild if the pull changed messages, package metadata, entry points, installed resources, dependencies, or package structure. If unsure, rebuild:

```cmd
colcon build --merge-install --symlink-install
install\setup.bat
```

## Testing

Pytest configuration is in:

```text
pytest.ini
```

Current test layout:

```text
tests/core/      Tests for vip_hpe_core. Should not require ROS or PyTorch.
tests/runtime/   Tests for replay/runtime logic. May require the ROS environment.
tests/ml/        Placeholder for future ML/PyTorch tests.
```

After setting up the ROS terminal, run:

```cmd
pytest -q tests/core tests/runtime
```

If `pytest` is not installed in the active Conda environment, install it with:

```cmd
conda install -c conda-forge pytest
```

The core dependency-boundary test checks that `vip_hpe_core` does not import ROS, PyTorch, Ultralytics, or ONNX Runtime.

## Notes for future development

The current live model node is still a placeholder. The current `pose_gt_inference_emulator_node` is intentionally used to rehearse the future model-inference flow:

```text
RadarFrame -> NumPy point cloud -> vip_hpe_core preprocessor -> pose output
```

When a deployed model is available, the future live inference node should reuse the same preprocessing config and publish the same `/pose/people` message type.

The training framework should live under `ml/` and should import `vip_hpe_core` for shared preprocessing. Do not add PyTorch training dependencies to the ROS runtime environment unless they are required for deployed inference.

# Contributing

The `main` branch is protected and should always remain stable, buildable, and suitable for others to pull from. Do not work directly on `main`. All development should happen on short-lived branches and be merged through pull requests.

## Branches

Use short-lived branches with one clear purpose. Before creating a branch, have a reasonably clear idea of what change you intend to make.

Use the following branch prefixes:

- `feature/...` — normal development branches. Open a PR into `main`.
- `fix/...` — bug-fix branches. Open a PR into `main`.
- `docs/...` — documentation-only branches.
- `exp/...` — experimental branches for ML trials, rough prototypes, or risky ideas. These may never merge.

Branches should be deleted after they are merged into `main`.

## Commits

Use one of the following commit prefixes:

- `feat:` new functionality
- `fix:` bug fix
- `test:` tests added or updated
- `docs:` documentation-only change
- `refactor:` code restructure without intended behaviour change
- `chore:` maintenance, cleanup, config, or minor repo-management changes

Examples:

```text
feat: add point cloud voxelisation helper
fix: handle empty radar frames
test: add pose transform unit test
docs: clarify ROS2 setup instructions
refactor: move preprocessing constants into shared core
chore: update gitignore
```

## Pull requests

All changes to `main` must go through a pull request.

PRs must be focused, reviewable, and linked to a clear task. Avoid large mixed-purpose PRs that change unrelated parts of the system.

Before opening a PR, pull the latest `main` and make sure your branch is up to date. Push your work at the end of each development session so progress is not left only on a local machine.

When a PR is opened, GitHub Actions will run automated tests. Some tests must pass before the PR can be merged. The current tests are basic, but more tests will be added over time. Passing the current tests is a minimum requirement, not proof that the change is correct.

## Shared core code

Changes to `hpe_vip_core` should be made carefully because this code may be used by both the ROS2 runtime and the PyTorch training framework.

If a PR changes `hpe_vip_core`, the PR description must explain:

- what changed;
- why it changed;
- whether the model input format changed;
- whether training and runtime behaviour may both be affected;
- whether tests were added or updated.

Avoid duplicating preprocessing logic separately in the ROS2 and PyTorch code. Shared preprocessing should live in `hpe_vip_core` wherever possible.