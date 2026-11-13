import os

from ament_index_python.packages import (
    get_package_prefix,
    get_package_share_directory,
)

from launch import LaunchDescription
from launch.actions import ExecuteProcess

from launch_ros.actions import Node


def generate_launch_description():

    # ============================================================
    # Package paths
    # ============================================================

    gazebo_share = get_package_share_directory(
        'whill_gazebo'
    )

    trajectory_share = get_package_share_directory(
        'whill_trajectory_control'
    )

    exact_prefix = get_package_prefix(
        'whill_exact_replay'
    )

    world_file = os.path.join(
        gazebo_share,
        'worlds',
        'exact_replay_validation.sdf'
    )

    profile_file = os.path.join(
        trajectory_share,
        'config',
        'fixed_profile.yaml'
    )

    # ============================================================
    # Gazebo environment
    # ============================================================

    model_path = os.path.join(
        gazebo_share,
        'models'
    )

    plugin_path = os.path.join(
        exact_prefix,
        'lib'
    )

    old_resource_path = os.environ.get(
        'IGN_GAZEBO_RESOURCE_PATH',
        ''
    )

    old_plugin_path = os.environ.get(
        'IGN_GAZEBO_SYSTEM_PLUGIN_PATH',
        ''
    )

    resource_path = (
        model_path
        + ':'
        + old_resource_path
    )

    system_plugin_path = (
        plugin_path
        + ':'
        + old_plugin_path
    )

    # ============================================================
    # Gazebo
    # ============================================================

    gazebo = ExecuteProcess(

        cmd=[
            'ign',
            'gazebo',
            '-v',
            '4',
            '-r',
            world_file,
        ],

        output='screen',

        additional_env={
            'IGN_GAZEBO_RESOURCE_PATH':
                resource_path,

            'IGN_GAZEBO_SYSTEM_PLUGIN_PATH':
                system_plugin_path,
        },
    )

    # ============================================================
    # ros_gz_bridge
    # ============================================================

    bridge = Node(

        package='ros_gz_bridge',

        executable='parameter_bridge',

        name='ros_gz_bridge',

        output='screen',

        arguments=[

            # Gazebo -> ROS
            '/clock@rosgraph_msgs/msg/Clock'
            '[ignition.msgs.Clock',

            # ROS -> Gazebo
            '/cmd_vel@geometry_msgs/msg/Twist'
            ']ignition.msgs.Twist',

            # ExactReplay triggers
            '/exact_replay/record@std_msgs/msg/Bool'
            ']ignition.msgs.Boolean',

            '/exact_replay/stop_record@std_msgs/msg/Bool'
            ']ignition.msgs.Boolean',

            '/exact_replay/start@std_msgs/msg/Bool'
            ']ignition.msgs.Boolean',

            # Physical robot ground truth
            '/model/four_wheel_robot/pose'
            '@tf2_msgs/msg/TFMessage'
            '[ignition.msgs.Pose_V',

            # Exact replay ground truth
            '/model/exact_replay_rig/pose'
            '@tf2_msgs/msg/TFMessage'
            '[ignition.msgs.Pose_V',

            # Physical IMU
            '/imu@sensor_msgs/msg/Imu'
            '[ignition.msgs.IMU',

            # Exact IMU
            '/exact/imu@sensor_msgs/msg/Imu'
            '[ignition.msgs.IMU',

            # Physical LiDAR point cloud
            '/lidar/points@sensor_msgs/msg/PointCloud2'
            '[ignition.msgs.PointCloudPacked',

            # Exact LiDAR point cloud
            '/exact/lidar/points@sensor_msgs/msg/PointCloud2'
            '[ignition.msgs.PointCloudPacked',
        ],

        remappings=[

            (
                '/model/four_wheel_robot/pose',
                '/ground_truth_pose'
            ),

            (
                '/model/exact_replay_rig/pose',
                '/exact/ground_truth_pose'
            ),
        ],
    )

    # ============================================================
    # Recorder
    # ============================================================
    
    recorder = Node(

        package='whill_experiment_recorder',

        executable='bag_recorder',

        name='bag_recorder',

        output='screen',

        parameters=[{
            'output_root':
                os.path.expanduser(
                    '~/ws_whill_sim/experiment_data'
                ),

            'trial_name': '',

            'profile_file':
                profile_file,

            'world_file':
                world_file,
        }],
    )

    # ============================================================
    # Fixed trajectory runner
    # ============================================================

    runner = Node(

        package='whill_trajectory_control',

        executable='fixed_profile_runner',

        name='fixed_profile_runner',

        output='screen',

        parameters=[
            profile_file
        ],
    )

    return LaunchDescription([
        gazebo,
        bridge,
        recorder,
        runner,
    ])