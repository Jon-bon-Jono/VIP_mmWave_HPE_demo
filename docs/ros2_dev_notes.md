# ROS 2 Development Notes

This document explains some of the ROS 2 concepts used in this repository. It is intended to help students understand what happens when they build, run, and modify the system.

## 1. ROS packages

A ROS package is the basic unit of a ROS project. A package can contain Python nodes, C++ nodes, custom message definitions, launch files, config files, tests, and other resources.

Each ROS package has a `package.xml` file. This file describes the package name, version, maintainer, license, dependencies, and build type.

This repository currently contains two ROS packages:

1. `vip_hpe_msgs`: defines custom ROS 2 messages.
2. `vip_hpe_runtime`: contains the Python runtime nodes, replay code, adapters, plotting code, launch files, and config files.

The split is deliberate. The message definitions are kept separate from the runtime implementation so that future replay nodes, live radar nodes, inference nodes, plotting nodes, and evaluation nodes can all share the same message types.

## 2. ament_python and ament_cmake

ROS 2 packages can use different build types.

Common build types include:

* `ament_python`: used for Python ROS 2 packages.
* `ament_cmake`: used for C++ packages, message packages, and mixed packages.

In this repository:

* `vip_hpe_runtime`: uses ament_python.
* `vip_hpe_msgs`: uses ament_cmake because it generates custom ROS 2 message bindings.

`vip_hpe_runtime` is an `ament_python` package because its code is installed as a Python package and its executable nodes are registered through `setup.py`.

## 3. What setup.py does

`setup.py` is the Python package installation recipe for `vip_hpe_runtime`.

It tells the build system:
* what the Python package is called
* which Python modules belong to it
* which scripts should become runnable ROS executables
* which launch/config/resource files should be installed

Two important sections are `entry_points` and `data_files`.

## 4. setup.py entry_points

The entry_points section defines runnable command-line programs.

For example:

```
entry_points={
    'console_scripts': [
        'radar_replay_node = vip_hpe_runtime.nodes.radar_replay_node:main',
    ],
}
```

This means:

Create a command called `radar_replay_node` and when someone runs  the command import `vip_hpe_runtime.nodes.radar_replay_node` and call `main()`

So when we run:
> `ros2 run vip_hpe_runtime radar_replay_node`

ROS 2 effectively runs the executable that calls:

```
from vip_hpe_runtime.nodes.radar_replay_node import main
main()
```

Editing the Python file referenced by an existing `entry_points` entry usually does not require a rebuild. For example, editing: `src\vip_hpe_runtime\vip_hpe_runtime\nodes\radar_replay_node.py` usually only requires restarting the node.

However, editing the `entry_points` values inside `setup.py` does require a rebuild. For example, you must rebuild if you:
* add a new executable node
* rename an executablechange which Python module an executable points to
* change which function should be called

## 5. setup.py data_files

The `data_files` section of `setup.py` installs non-Python resources such as:
* package.xml
* launch files
* config files
* resource marker files

For example, it installs: `src\vip_hpe_runtime\launch\replay_demo.launch.py` into the installed package share directory to enable this command:
> `ros2 launch vip_hpe_runtime replay_demo.launch.py`.

With `--symlink-install`, edits to existing launch/config files are usually picked up after restarting the launch command. If you add new launch/config files or change the install layout in `setup.py`, you must rebuild.

## 6. ros2 run

`ros2 run` starts one executable from one package.

For example, `ros2 run vip_hpe_runtime radar_replay_node` means:
* Find the installed ROS package called `vip_hpe_runtime`.
* Find the executable called `radar_replay_node`.
* Run that one executable.

Use `ros2 run` when you want to test or debug one packaged node. For example:

> `ros2 run vip_hpe_runtime radar_replay_node --ros-args -p pickle_path:="data\ll_replay\07_SW.pickle"`

## 7. Direct Python execution

A Python ROS 2 node can also sometimes be run directly. For example:

> `python src\vip_hpe_runtime\vip_hpe_runtime\nodes\radar_replay_node.py`

This works because a ROS 2 Python node is ultimately just a Python process using the rclpy library.

Direct Python execution can be useful for quick component-level debugging. However, it bypasses ROS package discovery, executable registration, launch files, installed resources, and some packaging assumptions.

Use direct Python execution for quick debugging only.

Use `ros2 run` to test that a node works as a packaged ROS executable.

Use `ros2 launch` to test the full multi-node system.

## 8. ros2 launch

`ros2 launch` starts a system described by a launch file.

For example:

> `ro2 launch vip_hpe_runtime replay_demo.launch.py pickle_path:="data\ll_replay\07_SW.pickle" start_index:=35000 playback_hz:=10.0 loop:=true`

This means:
* Find the installed package called `vip_hpe_runtime`.
* Look inside its installed launch directory.
* Load `replay_demo.launch.py`.
* Call `generate_launch_description()`.
* Execute the returned `LaunchDescription`.

A launch file is useful because a real ROS system usually contains multiple nodes. In this repository, the replay launch file currently starts:
* `radar_replay_node`
* `pose_gt_replay_node`
* `animated_plot_node`

This is easier and less error-prone than opening three terminals and manually running three commands.

## 9. What happens inside replay_demo.launch.py

ROS 2 Python launch files must provides a function called `generate_launch_description()`. This function returns a `LaunchDescription`. A `LaunchDescription` is basically a list of actions for `ros2 launch` to perform. 

The replay launch file does several things.

First, it declares launch arguments:

* `DeclareLaunchArgument('pickle_path', default_value='')`
* `DeclareLaunchArgument('start_index', default_value='0')`
* `DeclareLaunchArgument('playback_hz', default_value='10.0')`
* `DeclareLaunchArgument('loop', default_value='false')`

These can be overridden from the command line:

> `ros2 launch vip_hpe_runtime replay_demo.launch.py pickle_path:="data\ll_replay\07_SW.pickle" start_index:=35000`

Second, it creates launch configuration objects:

* `pickle_path = LaunchConfiguration('pickle_path')`
* `start_index = LaunchConfiguration('start_index')`

These are placeholders. They are resolved when the launch file actually runs.

Third, it starts nodes, for example:

```
Node(
    package='vip_hpe_runtime',
    executable='radar_replay_node',
    name='radar_replay_node',
    output='screen',
    parameters=[...],
)
```

Which is similar to running `ros2 run vip_hpe_runtime radar_replay_node` but with parameters supplied by the launch file.

The launch file defines which runnable programs are involved in the full replay system.


## 10. Node structure: rclpy.init, spin, and shutdown

Most Python ROS 2 nodes follow this structure:

```
def main(args=None):
    rclpy.init(args=args)

    node = SomeNode()

    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
```
* `rclpy.init()` initialises the ROS 2 Python client library for the current process. After this, the process can create ROS nodes, publishers, subscribers, timers, services, parameters, and other ROS entities.

* `rclpy.spin(node)` keeps the node alive and lets ROS 2 execute callbacks. Without spin, the node would usually start and then immediately exit. While spinning, ROS 2 waits for work such as:
  * timer callbacks
  * subscription messages
  * service requests
  * action events
  * parameter events
  * shutdown signals

* `rclpy.shutdown()` shuts down the ROS 2 context for the process

## 11. Parameters

ROS 2 parameters are runtime configuration values attached to a node.

Example:

```
self.declare_parameter("playback_hz", 10.0)
self.playback_hz = self.get_parameter("playback_hz").value
```

The first line declares a parameter called `playback_hz` with a default value of 10.0.

The second line reads the actual value. The actual value may be the default, or it may have been overridden by a launch file or command-line argument.

A parameter is better than a normal class variable when the value should be configurable at runtime. For example, this value can be set from a launch command: 
> `ros2 launch vip_hpe_runtime replay_demo.launch.py playback_hz:=5.0`

ROS 2 can also inspect parameters while a node is running.

A normal Python variable cannot be set from launch files, cannot be inspected by ROS 2 tools, and is invisible to the ROS graph.

## 12. Publishers and subscribers

A publisher sends messages on a topic.

Example:

> `self.publisher = self.create_publisher(RadarFrame, "/radar/points", 10)`

This declares that the node publishes `RadarFrame` messages on the topic `/radar/points`

A subscriber receives messages from a topic.

Example:

```
self.subscription = self.create_subscription(
    RadarFrame,
    "/radar/points",
    self.on_radar_frame,
    10,
)
```

This declares that the node wants to receive `RadarFrame` messages from `/radar/points` and when a message arrives ROS 2 calls `self.on_radar_frame(msg)`

This is how the replay nodes and plotting node communicate.

## 13. ROS graph

A ROS system is usually a graph of nodes connected by topics, services, and actions.

In this repository, the replay graph is roughly:

* `radar_replay_node`
  * publishes `/radar/points`

* `pose_gt_replay_node`
  * publishes `/pose/people`

* `animated_plot_node`
  * subscribes to  `/radar/points`
  * subscribes to `/pose/people`

The nodes do not directly call each other. They communicate through ROS topics.

This separation is important because later we can replace `radar_replay_node` with `live_radar_driver_node` and replace `pose_gt_replay_node` with `live_model_inference_node` while keeping the same topics and visualisation node.

## 14. Processes, nodes, and communication

In the current launch file, each executable is launched as its own operating-system process. On Windows, Task Manager may show separate Python processes.

A process owns resources such as:
* memory space
* open files
* network connections
* environment variables
* loaded Python interpreter
* loaded DLLs/libraries
* threads

Variables inside separate processes are not directly visible to each other.

ROS 2 enables communication between processes using topics, services, and actions.

In our current system, each process contains one ROS node. It is also possible for one process to contain multiple nodes, for example using a custom executor such as `rclpy.executors.MultiThreadedExecutor`. We do not need that yet.

The current design keeps each major component as a separate node/process because this is easier to debug and closer to the future live system.