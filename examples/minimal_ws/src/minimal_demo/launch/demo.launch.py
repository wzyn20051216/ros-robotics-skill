"""
demo.launch.py — minimal_demo 功能包启动文件

功能：
  - 同时启动 talker（发布者）和 listener（订阅者）节点
  - 从 config/demo_params.yaml 加载 talker 节点的参数
  - 禁用仿真时钟（use_sim_time=False），使用系统实时时钟

用法：
  ros2 launch minimal_demo demo.launch.py

可选参数（命令行覆盖）：
  ros2 launch minimal_demo demo.launch.py message_prefix:="Hi"
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """
    生成 LaunchDescription，ROS 2 launch 系统调用此函数
    来获取本次启动的所有动作（节点、参数、日志等）。
    """

    # ----------------------------------------------------------
    # 获取功能包共享目录路径（用于定位参数文件）
    # ----------------------------------------------------------
    pkg_share_dir = get_package_share_directory("minimal_demo")
    params_file = os.path.join(pkg_share_dir, "config", "demo_params.yaml")

    # ----------------------------------------------------------
    # 声明可在命令行覆盖的 launch 参数
    # 示例：ros2 launch minimal_demo demo.launch.py message_prefix:="Hi"
    # ----------------------------------------------------------
    declare_message_prefix_arg = DeclareLaunchArgument(
        name="message_prefix",
        default_value="Hello from minimal_demo",
        description="talker 节点发布消息的前缀字符串",
    )

    # ----------------------------------------------------------
    # 节点 1：talker（发布者）
    #   - 可执行文件：talker（由 CMakeLists.txt 编译生成）
    #   - 节点名称：talker_node
    #   - 参数来源：YAML 文件（通过 parameters 字段加载）
    #   - use_sim_time：False（使用真实时钟）
    # ----------------------------------------------------------
    talker_node = Node(
        package="minimal_demo",
        executable="talker",
        name="talker_node",
        output="screen",           # 将日志输出到终端
        emulate_tty=True,          # 保留彩色日志输出
        parameters=[
            params_file,           # 从 YAML 文件加载参数
            {
                # use_sim_time 内联参数（优先级高于 YAML）
                "use_sim_time": False,
            },
        ],
    )

    # ----------------------------------------------------------
    # 节点 2：listener（订阅者）
    #   - 无需参数文件，仅订阅 /chatter 话题
    # ----------------------------------------------------------
    listener_node = Node(
        package="minimal_demo",
        executable="listener",
        name="listener_node",
        output="screen",           # 将日志输出到终端
        emulate_tty=True,          # 保留彩色日志输出
        parameters=[
            {
                "use_sim_time": False,
            }
        ],
    )

    # ----------------------------------------------------------
    # 启动信息日志（在节点启动前打印提示）
    # ----------------------------------------------------------
    log_start = LogInfo(msg="正在启动 minimal_demo 演示（talker + listener）...")
    log_params = LogInfo(msg=["加载参数文件：", params_file])

    # ----------------------------------------------------------
    # 组装 LaunchDescription，按顺序执行动作
    # ----------------------------------------------------------
    return LaunchDescription([
        # 1. 声明可覆盖的参数
        declare_message_prefix_arg,

        # 2. 打印启动提示
        log_start,
        log_params,

        # 3. 启动节点
        talker_node,
        listener_node,
    ])
