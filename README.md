# VIP mmWave HPE Demo

This repo is a system for demonstrating real-time mmWave-radar-based human pose estimation and is designed for Windows 11 using Conda, RoboStack, ROS 2 Jazzy, and Python. 

The current runtime replays prerecorded mmWave point-cloud frames and Kinect pose ground-truth frames from pickle files. The same ROS topics are intended to be reused later by live radar and live inference nodes. 

It separates the runtime into five layers:

1. **Data replay layer**: loads pickle files and normalises point cloud / Kinect pose arrays.
2. **Interface layer**: custom ROS 2 messages for radar frames and 3D human poses.
3. **Adapter layer**: converts parsed replay frames to ROS messages and back to NumPy arrays for plotting.
4. **Runtime node layer**: simulated radar driver, simulated inference node, and placeholder live inference node.
5. **Visualisation / launch layer**: animated Matplotlib 3D plot and launch/config files.

The prerecorded system deliberately uses the same ROS topics that later live nodes should use:

- `/radar/points` publishes `vip_hpe_msgs/msg/RadarFrame`.
- `/pose/people` publishes `vip_hpe_msgs/msg/PersonPose3DArray`.
- `/debug/replay_status` publishes a minimal status string.

## Windows 11 ROS 2 Development Setup

### 1. Create the Conda environment
Open a new command prompt as administrator in the repo root: `VIP_MMWAVE_HPE_DEMO/`. 

Create the Conda environment from the provided YAML file: 
> `conda env create -f vip_ros2_jazzy_dev.yml`
 
Activate the environment:
> `conda activate vip_ros2_jazzy_dev`
   * This changes your terminal environment so that `python`, `ros2`, `colcon`, and the RoboStack ROS 2 packages are available.
  
### 2. Build the ROS 2 workspace

For the first build, you must open the terminal as Administrator. The recommended build uses symbolic links, and Windows may block symlink creation in a normal terminal.

From the repository root, run:

> `colcon build --merge-install --symlink-install`

  * colcon builds the ROS 2 packages in the workspace. This repository currently contains two ROS 2 packages:
    1. vip_hpe_msgs: Custom ROS 2 message definitions.
    2. vip_hpe_runtime: Python runtime nodes, replay loaders, adapters, plotting code, launch files,

  * `--symlink-install` makes development faster because many installed files point back to the source instead of being copied. With this setup, normal edits to Python files, launch files, and config files in src/vip_hpe_runtime/ are usually picked up after restarting the node/launch. You do not need to rebuild after every Python edit. See 'When to Rebuild' for more info. 

### 3. Setup each new terminal

Perform these steps every time you open a new terminal in the repo root.

Run:
> `conda activate vip_ros2_jazzy_dev`

Load the built ROS 2 workspace into the current terminal environment:
> `install\setup.bat`
   * This adds the installed workspace to your terminal environment so ROS 2 can find the local packages built in this workspace, such as `vip_hpe_msgs` and `vip_hpe_runtime`.

Force Python to import the live source version of `vip_hpe_runtime` instead of the installed/build copy:
> `set PYTHONPATH=%CD%\src\vip_hpe_core;%CD%\src\vip_hpe_runtime;%PYTHONPATH%`
  * This helps ensure that edits to Python files under: `src\vip_hpe_runtime\vip_hpe_runtime\` are picked up after restarting the node/launch, without running colcon build again.

### 4. Download sample prerecorded data

Download sample pre-recorded data from:
Place it here: `data/ll_replay/`

### 5. Launch the replay demo

Launch the system by executing: 
> `ros2 launch vip_hpe_runtime replay_demo.launch.py pickle_path:="data/ll_replay/07_SW.pickle" start_index:=35000 playback_hz:=10.0 loop:=true`

Steps 3, 6 and 7 must be performed every time you open a new terminal.

## When to Rebuild
You must rebuild if you modify:
* src\vip_hpe_msgs\msg\*.msg
* src\vip_hpe_msgs\CMakeLists.txt
* src\vip_hpe_msgs\package.xml
* src\vip_hpe_runtime\setup.py
* src\vip_hpe_runtime\package.xml

You must also rebuild if you add a new Python node that should become a new ROS executable. For example, if you add: `src\vip_hpe_runtime\vip_hpe_runtime\nodes\new_debug_node.py` and want to run it as: `ros2 run vip_hpe_runtime new_debug_node` then you must add it to `entry_points` in `src\vip_hpe_runtime\setup.py` and rebuild.

You usually do not need to rebuild for normal edits to existing Python source files under: `src\vip_hpe_runtime\vip_hpe_runtime\`. Just stop and restart the running node or launch command.

You usually do not need to rebuild when adding helper Python modules that are imported by existing nodes, as long as those modules live under the `vip_hpe_runtime` Python package and the PYTHONPATH source override is active.

After pulling new changes, rebuild if the pull changed message definitions, package metadata, dependencies, entry points, or package installation rules.

If changes to the code aren't manifesting at runtime, rebuild. 

When in doubt, rebuild.

## Configure pickle path

Edit:

```text
src/vip_hpe_runtime/config/replay_demo.yaml
```

Set `pickle_path` to your actual `.pickle` file.

## Run the replay demo

```powershell
ros2 launch vip_hpe_runtime replay_demo.launch.py pickle_path:=C:/path/to/07_SW.pickle start_index:=35000 playback_hz:=10.0
```

A Matplotlib 3D animation window should open. The plotter subscribes to point cloud and pose topics rather than reading the pickle directly.

## Run nodes manually

Terminal 1:

```powershell
conda activate vip_ros2_jazzy_dev
.\install\setup.bat
ros2 run vip_hpe_runtime radar_replay_node --ros-args -p pickle_path:=C:/path/to/07_SW.pickle -p start_index:=35000
```

Terminal 2:

```powershell
conda activate vip_ros2_jazzy_dev
.\install\setup.bat
ros2 run vip_hpe_runtime pose_gt_replay_node --ros-args -p pickle_path:=C:/path/to/07_SW.pickle -p start_index:=35000
```

Terminal 3:

```powershell
conda activate vip_ros2_jazzy_dev
.\install\setup.bat
ros2 run vip_hpe_runtime animated_plot_node
```

## Notes

This is a skeleton, not the final runtime. The live radar driver and live model inference node are placeholders by design. The important part is that replay and future live nodes publish the same interfaces.

