# 多机器人系统参考

## 第一原则

多机器人问题通常出在 **命名空间隔离、TF 冲突和网络配置** 三个层面，而不是单机器人功能本身的问题。先确认单机器人独立运行正常，再排查多机共存时的冲突。

## 命名空间隔离策略

### launch 中设置命名空间

最常用的隔离方式是通过 `PushRosNamespace` 或 `Node` 的 `namespace` 参数：

```python
from launch import LaunchDescription
from launch.actions import GroupAction, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import PushRosNamespace, Node

def generate_launch_description():
    robot_ns = LaunchConfiguration('namespace')

    declare_ns = DeclareLaunchArgument(
        'namespace', default_value='robot1',
        description='机器人命名空间'
    )

    robot_group = GroupAction([
        PushRosNamespace(robot_ns),

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_desc}],
            # TF topic 需要特殊处理（见下方说明）
            remappings=[
                ('/tf', 'tf'),
                ('/tf_static', 'tf_static'),
            ],
        ),

        Node(
            package='nav2_bringup',
            executable='bringup_launch.py',
            # Nav2 内部参数也需要配合命名空间
            parameters=[{
                'use_namespace': True,
                'namespace': robot_ns,
            }],
        ),
    ])

    return LaunchDescription([declare_ns, robot_group])
```

### 多机器人启动

```bash
# 机器人 1
ros2 launch my_robot bringup.launch.py namespace:=robot1

# 机器人 2
ros2 launch my_robot bringup.launch.py namespace:=robot2
```

## TF 隔离

### 问题本质

默认情况下所有节点向全局 `/tf` 和 `/tf_static` 发布变换。多机器人的 `odom -> base_link` 等变换会互相覆盖。

### 方案 A：frame_prefix（推荐）

每台机器人的所有 frame 加上前缀：

```yaml
# robot1 的参数
robot_state_publisher:
  ros__parameters:
    frame_prefix: "robot1/"
    # 发布的 frame 变为 robot1/base_link, robot1/odom 等
```

TF 树结构：
```
map
├── robot1/odom -> robot1/base_link -> robot1/laser_frame
└── robot2/odom -> robot2/base_link -> robot2/laser_frame
```

注意事项：
- Nav2、AMCL 等节点的 `global_frame`、`robot_base_frame` 参数都需要加前缀
- 传感器消息的 `header.frame_id` 也需要与前缀匹配
- URDF 中的 frame 名称不需要改，`frame_prefix` 会自动添加

### 方案 B：独立 TF topic

每台机器人使用独立的 TF topic（通过 remap）：

```python
Node(
    package='robot_state_publisher',
    executable='robot_state_publisher',
    namespace='robot1',
    remappings=[
        ('/tf', '/robot1/tf'),
        ('/tf_static', '/robot1/tf_static'),
    ],
)
```

缺点：需要所有使用 TF 的节点都做相同的 remap，容易遗漏。

## 跨机通信配置

### 方案 1：共享 DDS Domain（同一网络）

所有机器人使用相同的 `ROS_DOMAIN_ID`，通过命名空间隔离：

```bash
# 所有机器中
export ROS_DOMAIN_ID=0
```

优点：简单，所有节点可以互相发现。
缺点：网络流量大，所有 topic 对所有机器可见。

### 方案 2：多 Domain + topic_bridge

每台机器人独立 Domain，中央节点做桥接：

```bash
# 机器人 1
export ROS_DOMAIN_ID=1

# 机器人 2
export ROS_DOMAIN_ID=2

# 中央控制站
# 使用 domain_bridge 桥接需要共享的 topic
ros2 run domain_bridge domain_bridge config.yaml
```

```yaml
# domain_bridge config.yaml
topics:
  /robot1/odom:
    type: nav_msgs/msg/Odometry
    from_domain: 1
    to_domain: 0
  /robot2/odom:
    type: nav_msgs/msg/Odometry
    from_domain: 2
    to_domain: 0
```

### 方案 3：Discovery Server（大规模推荐）

使用 Fast DDS Discovery Server 减少组播流量：

```bash
# 在中央服务器启动 discovery server
fastdds discovery -i 0 -l 192.168.1.100 -p 11811

# 每台机器人配置
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DISCOVERY_SERVER=192.168.1.100:11811
```

优点：减少网络发现开销，适合大规模部署（>5 台机器人）。

## 时间同步方案

多机器人系统中时间同步至关重要，TF、传感器融合都依赖一致的时间戳。

### 实物环境：chrony/NTP

```bash
# 在主机（时间服务器）上
sudo apt install chrony
# /etc/chrony/chrony.conf 添加：
# local stratum 10
# allow 192.168.1.0/24

# 在每台机器人上
# /etc/chrony/chrony.conf 添加：
# server 192.168.1.100 iburst

# 检查同步状态
chronyc tracking
chronyc sources -v
# offset 应在 1ms 以内
```

### 仿真环境：use_sim_time

```bash
# 所有节点统一使用仿真时间
ros2 launch my_robot bringup.launch.py use_sim_time:=true
```

所有节点参数中设置 `use_sim_time: true`，确保时间源一致。

## ROS_DOMAIN_ID 规划

| 场景 | 建议方案 |
|------|----------|
| 2~3 台机器人，同一网络 | 共享 Domain + 命名空间隔离 |
| 4~10 台机器人 | 每组一个 Domain + bridge |
| >10 台或跨网段 | Discovery Server |
| 开发调试 | 每人不同 DOMAIN_ID 避免干扰 |

`ROS_DOMAIN_ID` 有效范围：0~232（推荐 0~101），每个 ID 占用不同的 UDP 端口。

## 常见冲突排查

### topic 名冲突

```bash
# 检查是否有未加命名空间的 topic
ros2 topic list | grep -v "robot[0-9]"
# 不应出现裸的 /cmd_vel, /odom 等
```

### TF 冲突

```bash
# 检查是否有多个节点发布同一个变换
ros2 run tf2_tools view_frames
# 在 PDF 中检查是否有重复的 frame 名

ros2 topic echo /tf --field transforms[0].header.frame_id
# 确认每个变换的 frame 都有正确的前缀
```

### 参数覆盖

- 多台机器人共用同一个参数文件但参数值应该不同（如机器人 ID、初始位姿）
- 使用 launch 参数或命名空间自动区分
- 确认每台机器人的参数文件路径或参数值是独立的

### map frame 共享问题

- 如果多台机器人共享同一张地图，`map` frame 应该是全局唯一的
- 每台机器人各自维护 `map -> robotX/odom` 的变换
- 如果各自建图，考虑使用独立的 map frame（如 `robot1/map`, `robot2/map`）

```bash
# 验证 map frame 的发布情况
ros2 run tf2_ros tf2_echo map robot1/odom
ros2 run tf2_ros tf2_echo map robot2/odom
```

## 官方与高星参考

- Nav2 多机器人文档：<https://docs.nav2.org/tutorials/docs/multi_robot.html>
- ROS 2 多机器人设计：<https://design.ros2.org/articles/unique_namespaces.html>
- domain_bridge：<https://github.com/ros2/domain_bridge>
- Fast DDS Discovery Server：<https://fast-dds.docs.eprosima.com/en/latest/fastdds/discovery/discovery_server.html>
- ROS 2 命名空间与重映射：<https://design.ros2.org/articles/topic_and_service_names.html>
- 多机器人 SLAM 方案总结：<https://github.com/MAPIRlab/multi-robot-slam>
- ROS 2 REP-105 坐标系约定：<https://www.ros.org/reps/rep-0105.html>
