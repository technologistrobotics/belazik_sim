# Copyright 2022 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from ament_index_python.packages import get_package_share_directory, get_package_prefix


from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription, RegisterEventHandler, DeclareLaunchArgument, SetEnvironmentVariable
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


import xacro


def generate_launch_description():
   
    package_name = 'robot_sim'
   

    #gazebo begin

    


    default_world = os.path.join(
        get_package_share_directory(package_name),
        'worlds',
        'empty.world'
        )    

    world_arg = DeclareLaunchArgument(
        'world',
        default_value=default_world,
        description='World to load'
        )
        #launch the sim
    gazebo = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')]),
                    launch_arguments={'gz_args': f'-r -v4 {default_world}', 'on_exit_shutdown': 'true'}.items()
             )
        #spawn the robot
    spawn_entity = Node(package='ros_gz_sim', executable='create',
                        arguments=['-topic', '/robot_description',
                                   '-entity', 'robot', '-z', '0.1'],
                        output='screen')
        #bridge
    bridge_params = os.path.join(get_package_share_directory(package_name),'config','gz_bridge.yaml')
    ros_gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            '--ros-args',
            '-p',
            f'config_file:={bridge_params}',
        ]
    )
    #gazebo end

    #urdf begin
    urdf_path = os.path.join(
        get_package_share_directory(package_name))

    xacro_file = os.path.join(urdf_path,
                              'urdf',
                              'belazik_drive.xacro.urdf')
    

    doc = xacro.parse(open(xacro_file))
    xacro.process_doc(doc)
    params = {'robot_description': doc.toxml()}

    #urdf end 

    #control begin
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[params]
    )


    load_joint_state_broadcaster = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active',
             'joint_state_broadcaster'],
        output='screen'
    )
    slam_node = ExecuteProcess(
        cmd=['ros2', 'launch', 'robot_sim', 'online_async_launch.py', 'use_sim_time:=True',],
        output='screen'
    )
    nav_node = ExecuteProcess(
        cmd=['ros2', 'launch', 'robot_sim', 'navigation_launch.py', 'use_sim_time:=True',],
        output='screen'
    )
    load_controller = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active',
             'ackermann_controller' ],
        output='screen'
    )

    #control end
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=[
            '-d',
            os.path.join(urdf_path, 'config/config.rviz'),
        ],
        output='screen',
    )

    #multiplexer begin
    twist_mux_params = os.path.join(get_package_share_directory(package_name),'config','twist_mux.yaml')

    twist_mux = Node(
            package="twist_mux",
            executable="twist_mux",
            parameters=[twist_mux_params, {'use_sim_time': True}, {'use_stamped': True}],
            remappings=[('/cmd_vel_out','/robot/cmd_vel')]  
        )
    #multiplexer end

    #finally launch everything
    return LaunchDescription([
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=spawn_entity,
                on_exit=[load_joint_state_broadcaster], #we should load joint state broadcaster only after the robot appears
            )
        ),
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=load_joint_state_broadcaster,
                on_exit=[load_controller],  #the same with contoller 
            )
        ),
      
        gazebo,
        twist_mux,
        rviz,
        node_robot_state_publisher,
        spawn_entity,
        #slam_node,
        #nav_node
        ros_gz_bridge,
    ])
