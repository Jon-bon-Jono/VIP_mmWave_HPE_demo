from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pickle_path = LaunchConfiguration('pickle_path')
    start_index = LaunchConfiguration('start_index')
    end_index = LaunchConfiguration('end_index')
    playback_hz = LaunchConfiguration('playback_hz')
    loop = LaunchConfiguration('loop')

    shared_replay_params = {
        'pickle_path': pickle_path,
        'start_index': ParameterValue(start_index, value_type=int),
        'end_index': ParameterValue(end_index, value_type=int),
        'playback_hz': ParameterValue(playback_hz, value_type=float),
        'loop': ParameterValue(loop, value_type=bool),
    }

    return LaunchDescription([
        DeclareLaunchArgument('pickle_path', default_value='', description='Path to Living Lab pickle file'),
        DeclareLaunchArgument('start_index', default_value='0', description='First frame index to replay'),
        DeclareLaunchArgument('end_index', default_value='-1', description='Exclusive end frame index; -1 means file end'),
        DeclareLaunchArgument('playback_hz', default_value='10.0', description='Replay publication rate'),
        DeclareLaunchArgument('loop', default_value='false', description='Loop replay range'),

        Node(
            package='vip_hpe_runtime',
            executable='radar_replay_node',
            name='radar_replay_node',
            output='screen',
            parameters=[shared_replay_params],
        ),
        Node(
            package='vip_hpe_runtime',
            executable='pose_gt_replay_node',
            name='pose_gt_replay_node',
            output='screen',
            parameters=[shared_replay_params],
        ),
        Node(
            package='vip_hpe_runtime',
            executable='animated_plot_node',
            name='animated_plot_node',
            output='screen',
        ),
    ])

