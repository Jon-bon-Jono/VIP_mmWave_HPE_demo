ROS Package: basic unit of a ROS project. Our packages are vip_hpe_msgs and vip_hpe_runtime. Eacg package has a package.xml file. 

ament_python package: ROS 2 package whose code is installed as a Python package. ROS 2 has several build types. Common ones are ament_python and ament_cmake (for C++ packages, message packages). vip_hpe_runtime is ament because it contains python nodes. 

`conda activate vip_ros2_jazzy_dev`, conda changes your terminal environment so that `python`, `ros2` and `colcon` can be executed.

`colcon build --merge-install` colcon reads the ROS packages, sees that vip_hpe_runtime is an ament_python package, and uses setup.py to install it into the workspace. Run this after editing the code. Don't need to run this for every new terminal.

`.\install\setup.bat` adds the installed workspace to your terminal environment so ROS 2 can find the package. Run this each new terminal. 

ros2 launch vip_hpe_runtime replay_demo.launch.py pickle_path:="C:\Users\GSBME\SmartCupStudy\Unified_network\data_sets\UNSW-PANOPTES\UNSW-PANOPTES-ETL-Pipeline\data\prepared\pc_raw_hpe_act\07_SW.pickle" start_index:=35000 playback_hz:=10.0 loop:=true

`setup.py` - Python package installation recipe
> entry_points - defines individual runnable programs by creating commands such as `radar_replay_node` and when someone runs the command, import `vip_hpe_runtime.nodes.radar_replay_node` and call `main()`. So when we run `ros2 run vip_hpe_runtime radar_replay_node` ROS 2 effectively does this `from vip_hpe_runtime.nodes.radar_replay_node import main; main()`
> data_files - installs the launch file `replay_demo.launch.py` into the python packages installed share directory

`ros2 run vip_hpe_runtime radar_replay_node` run starts on executable from one package

`ros2 launch vip_hpe_runtime replay_demo.launch.py` runs a system described by a launch file:
1. Find the installed packag `vip_hpe_runtime`
2. Look inside its launch directory
3. Load replay_demo.launch.py
4. Call generate_launch_descriptions()
5. Execute the returned LaunchDescription
> ros2 launch expects the launchfile to provide that function. It returns a LaunchDescription, which is basically a list of things the launch system should do.

`replay_demo.launch.py` - defines which runable programs involved in the full system
> declares launch arguments (you can override from comman line)
> creates launch config objects (placeholders to be resolved when the launchfile runs)
> starts the radar replay nodes. For example ` Node(package='vip_hpe_runtime', executable='radar_replay_node', ...` is equivalent to launching `ros2 run vip_hpe_runtime radar_replay_node`


`rclpy.init()`: init ROS2 python client library for the current process. Process becomes an ROS participant which can create nodes, publishers, subcscribers, timners, services, etc. E.g. create node after this. 

`rclpy.spin(node)`: keeps the node alive and lets ROS execute callbacks. Without this, a node would start then immediately exit. This enters an event loop. While spinning, ROS waits for work such as timer callback ready, subscription message received, service request received, action event received, parameter event received, shutdown signal received. 

`rclpy.shutdown()`: shuts down ROS context for the process


`declare_parameter`: creates a parameter that belongs to the node. Give it a name and default value. Basically a runtime configuration attached to a node and can be set from launch. Why not just use a regular class variable?: ROS2 doesn't know about the variable, can't be set from the launch file or command line, can't be inspected while the node is running.
`get_parameter`: reads parameter from the node

`self.declare_parameter("playback_hz", 10.0)`
`self.playback_hz = self.get_parameter("playback_hz").value`
 --> declares the parameter with a default. Then read the actual value. 

`create_publisher`: creates a publisher object for a topic. Declares that the node publishes messages of a specific type (e.g. RadarFrame) over a named topic (e.g. "/radar/points"). Anyone interested in the topic can subscribe. 

 `create_subscription`: creates subscriber object for a topic. Declares that the node wants to receive messages of a specific type, from a specific topic and when a message arrives, call a specific callback function. 


This is a bit of a bottleneck because it takes a couple of minutes to execute: `colcon build --merge-install`. Is this build step necessary in order to launch the system each time I modify the code? Can I launch an 'unbuilt' system?

ROS graph of nodes. 
Each executable is launched as its own OS process (task manager sees separate Python processes). In our launch file so far, each process has one node, but multiple nodes can live in one process (via `rclpy.executors.MultiThreadedExecutor()`).

Processes own resources such as memory space, open files, network connections, environment variables, loaded Python interpreter, loaded DLLs/libraries, threads (executable stream of instructions, OS scheduler decides which threads run on which CPU core and when). Variables inside separate processes are not directly visible to one another. ROS2 enables inter-process communication (via topics).

The ROS inference node should not hardcode preprocessing parameters. It should load the same preprocessing.yaml that was used during training/export.

vip_hpe_core should be lower-level than vip_hpe_runtime. If vip_hpe_core needs something from vip_hpe_runtime, that thing probably belongs in vip_hpe_core instead. The dependency direction should remain as `vip_hpe_runtime  --->  vip_hpe_core` never the other way around.

Rebuild when you change: src\vip_hpe_core\setup.py
src\vip_hpe_core\package.xml
src\vip_hpe_runtime\package.xml

Need to do this aswell: set PYTHONPATH=%CD%\src\vip_hpe_core;%CD%\src\vip_hpe_runtime;%PYTHONPATH%

This repo should be not hardcoded as a replayer.

Do we create a new launch file for the version of the demo which doesn't perform replay? Would we create a new launch file for each different radar driver

Handling of timestamps is wrong in the replay system.

How could this be extended to perform:
* data collection?
* 2D / 3D pose estimation?
* pose estimation?
* Different skeleton topologies?
* Different radars?

TODO: 
* Wire replay_demo.yaml to the launch file so that we can use the yaml file to override launch arguments, instead of having to do this on the command line
* How we should handle future use cases. Should we create a new launch file for the live system which streams radar dat and performs pose estimation, or should we parameterise the current launch file to handle both use cases? What about when we want to use different radars? Should we have one launch file per radar? Or parameterise one shared launch file?
* AnimatedPosePointCloudPlot.draw should be able to handle different pose formats. It currently supports Kinect's 32-point topology, the MM-Fi dataset uses a 17-point topology. 
* Implement point cloud preprocessing to convert RadarFrame.points to a format expected by the pose estimation model. This could be called In LiveModelInferenceNode._run_model. 
* More unit tests