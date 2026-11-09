import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    sim_pkg_dir = get_package_share_directory('reactive_robot_sim')
    
    sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(sim_pkg_dir, 'launch', 'reactive_robot_sim.launch.py')
        )
    )

    avoidance_node = Node(
        package='reactive_robot',
        executable='avoidance_node',
        name='reactive_obstacle_avoidance',
        output='screen',
        parameters=[{
            'max_linear_speed': 0.22,
            'min_linear_speed': 0.05,
            'max_angular_speed': 0.8,
            'safe_distance': 0.75
        }]
    )

    return LaunchDescription([
        sim_launch,
        avoidance_node
    ])
