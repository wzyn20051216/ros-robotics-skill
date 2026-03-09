# Gazebo 仿真集成参考

## 第一原则

Gazebo 问题通常出在：模型描述(SDF/URDF)、传感器插件配置、物理参数、ros_gz_bridge 桥接，而不是仿真器本身。

---

## Gazebo Classic vs Ignition/Gz

| ROS 2 发行版 | 推荐版本 | 包名前缀 |
|---|---|---|
| Humble | Classic 11 / Gz Fortress | `gazebo_ros` / `ros_gz` |
| Jazzy | Gz Harmonic | `ros_gz` |

```bash
sudo apt install ros-jazzy-ros-gz          # Gz Harmonic
sudo apt install ros-humble-gazebo-ros-pkgs # Classic
```

---

## 传感器仿真配置

### LiDAR (SDF gpu_lidar)

```xml
<sensor name="lidar" type="gpu_lidar">
  <topic>scan</topic>
  <update_rate>10</update_rate>
  <lidar>
    <scan><horizontal>
      <samples>640</samples><resolution>1</resolution>
      <min_angle>-3.14159</min_angle><max_angle>3.14159</max_angle>
    </horizontal></scan>
    <range><min>0.08</min><max>10.0</max><resolution>0.01</resolution></range>
  </lidar>
  <always_on>true</always_on>
</sensor>
```

### Camera (URDF Gazebo 插件)

```xml
<gazebo reference="camera_link">
  <sensor name="camera" type="camera">
    <update_rate>30</update_rate>
    <camera>
      <horizontal_fov>1.396</horizontal_fov>
      <image><width>640</width><height>480</height><format>R8G8B8</format></image>
      <clip><near>0.02</near><far>100</far></clip>
    </camera>
    <plugin name="camera_ctrl" filename="libgazebo_ros_camera.so">
      <ros><remapping>image_raw:=camera/image_raw</remapping></ros>
      <frame_name>camera_optical_link</frame_name>
    </plugin>
  </sensor>
</gazebo>
```

### IMU (SDF)

```xml
<sensor name="imu_sensor" type="imu">
  <always_on>true</always_on>
  <update_rate>100</update_rate>
  <imu>
    <angular_velocity><x><noise type="gaussian"><mean>0</mean><stddev>2e-4</stddev></noise></x></angular_velocity>
    <linear_acceleration><x><noise type="gaussian"><mean>0</mean><stddev>1.7e-2</stddev></noise></x></linear_acceleration>
  </imu>
</sensor>
```

---

## 物理参数调优

```xml
<physics name="default_physics" type="ode">
  <max_step_size>0.001</max_step_size>        <!-- 步长越小越精确但越慢 -->
  <real_time_factor>1.0</real_time_factor>     <!-- 1.0=实时 -->
  <ode><solver><type>quick</type><iters>50</iters></solver></ode>
</physics>
```

**sim-to-real 验证：** 对比传感器频率/噪声、控制延迟、碰撞检测精度。

---

## ros_gz_bridge 配置

```yaml
- topic_name: "/scan"
  ros_type_name: "sensor_msgs/msg/LaserScan"
  gz_type_name: "gz.msgs.LaserScan"
  direction: GZ_TO_ROS
- topic_name: "/cmd_vel"
  ros_type_name: "geometry_msgs/msg/Twist"
  gz_type_name: "gz.msgs.Twist"
  direction: ROS_TO_GZ
```

| ROS 2 类型 | Gz 类型 |
|---|---|
| `geometry_msgs/msg/Twist` | `gz.msgs.Twist` |
| `sensor_msgs/msg/LaserScan` | `gz.msgs.LaserScan` |
| `sensor_msgs/msg/Image` | `gz.msgs.Image` |
| `sensor_msgs/msg/Imu` | `gz.msgs.IMU` |
| `nav_msgs/msg/Odometry` | `gz.msgs.Odometry` |

---

## Launch 集成示例

```python
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg_gz = get_package_share_directory('ros_gz_sim')
    world = os.path.join(get_package_share_directory('my_robot'), 'worlds', 'my_world.sdf')

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_gz, 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': ['-r ', world]}.items(),
    )
    spawn = Node(package='ros_gz_sim', executable='create',
                 arguments=['-name', 'my_robot', '-topic', 'robot_description'])
    bridge = Node(package='ros_gz_bridge', executable='parameter_bridge',
                  arguments=['/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan'])
    return LaunchDescription([gz_sim, spawn, bridge])
```

---

## 常见故障

| 现象 | 原因 | 排查 |
|---|---|---|
| 模型加载失败 mesh 错误 | mesh 路径错误 | 检查 `GZ_SIM_RESOURCE_PATH` |
| 传感器 topic 不可见 | 桥接未配置 | `gz topic -l` 确认 Gz 侧有数据 |
| 实时率远低于 1.0 | 模型复杂/步长太小 | 简化碰撞模型，增大 step_size |
| 机器人穿透地面 | 碰撞/惯性参数缺失 | 检查 `<collision>` 和 `<inertial>` |
| bridge 报 No such interface | Gz 消息类型名拼写错误 | 核对 `gz msg --list` |

---

## 官方与高星参考

- Gz Sim 文档: <https://gazebosim.org/docs>
- ros_gz GitHub: <https://github.com/gazebosim/ros_gz>
- gazebo_ros_pkgs: <https://github.com/ros-simulation/gazebo_ros_pkgs>
- SDF 规范: <https://sdformat.org/spec>
