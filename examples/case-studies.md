# 真实案例

## 案例 1：ROS 1 `catkin_ws` 构建失败

### 输入问题

用户反馈：`catkin_make` 总报依赖或链接错误，不确定该改 `package.xml` 还是 `CMakeLists.txt`。

### skill 的处理路径

1. 先运行 `scripts/detect_ros_workspace.py`
2. 再运行 `scripts/check_ros_workspace_consistency.py`
3. 加载 `references/ros1-catkin.md`
4. 优先对齐 `package.xml` 与 `CMakeLists.txt`

### 输出动作

- 标记缺失依赖
- 给出最小修复点
- 给出 `rosdep`、`catkin build` / `catkin_make` 的验证命令

## 案例 2：ROS 2 模型能加载，但 TF / RViz 不对

### 输入问题

用户反馈：RViz 能看到机器人，但方向错、传感器位置不对，导航也异常。

### skill 的处理路径

1. 加载 `references/robot-description-and-tf.md`
2. 核对 `robot_description`、`joint_states`、mesh 路径、Fixed Frame
3. 核对 `base_link`、`odom`、`map` 和传感器 frame

### 输出动作

- 指出可能错误的外参、关节轴或 frame 命名
- 给出最小复测链路
- 解释为什么应先修 TF，再看导航问题

## 案例 3：Nav2 已激活，但底盘不动

### 输入问题

用户反馈：规划正常、路径有了、Nav2 active，但车就是不走。

### skill 的处理路径

1. 加载 `references/navigation2.md`
2. 检查 `/cmd_vel` 是否生成
3. 检查底盘是否订阅到命令
4. 检查速度单位、QoS、急停和超时保护

### 输出动作

- 给出最可能的 3 个根因
- 每个根因给 1~2 个验证动作
- 给出底盘侧和导航侧的最小修改建议

## 案例 4：QoS 不兼容导致 topic 丢帧

### 输入问题

用户反馈：发布者和订阅者节点都在运行，`ros2 topic list` 能看到 topic，但订阅者始终收不到消息，或收到的频率远低于预期。

### skill 的处理路径

1. 加载 `references/dds-qos-networking.md`
2. 用 `ros2 topic info /target_topic -v` 检查发布者和订阅者的 QoS 设置
3. 重点对比 Reliability（RELIABLE vs BEST_EFFORT）和 Durability（TRANSIENT_LOCAL vs VOLATILE）
4. 运行 `ros2 doctor --report` 查看是否有 QoS 兼容性警告

### 输出动作

- 指出不兼容的 QoS 策略组合（如发布者 BEST_EFFORT + 订阅者 RELIABLE 会导致完全收不到）
- 给出具体修复建议：

```python
# 修复示例：将订阅者 QoS 改为兼容设置
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy

qos = QoSProfile(
    depth=10,
    reliability=ReliabilityPolicy.BEST_EFFORT,   # 匹配发布者
    durability=DurabilityPolicy.VOLATILE,          # 匹配发布者
)
self.subscription = self.create_subscription(
    msg_type, '/target_topic', self.callback, qos)
```

- 给出验证命令：

```bash
# 验证消息是否恢复正常
ros2 topic hz /target_topic
ros2 topic echo /target_topic --once
```

## 案例 5：Docker 中运行 ROS 2 无法发现节点

### 输入问题

用户反馈：两个 Docker 容器各运行一个 ROS 2 节点，`ros2 node list` 在对方容器中看不到节点，`ros2 topic list` 也看不到对方的 topic。

### skill 的处理路径

1. 加载 `references/docker-ros.md`
2. 检查 Docker 网络模式（bridge vs host）
3. 检查 `ROS_DOMAIN_ID` 是否一致
4. 检查 DDS 实现和组播配置

### 输出动作

- 方案 A：使用 host 网络模式（最简单）

```bash
# 两个容器都使用 host 网络
docker run --network=host --ipc=host \
  -e ROS_DOMAIN_ID=0 \
  my_ros2_image
```

- 方案 B：bridge 网络 + CycloneDDS unicast 配置（适合生产环境）

```xml
<!-- cyclonedds.xml -->
<CycloneDDS>
  <Domain>
    <General>
      <DontRoute>true</DontRoute>
    </General>
    <Discovery>
      <Peers>
        <Peer address="container1_ip"/>
        <Peer address="container2_ip"/>
      </Peers>
      <ParticipantIndex>auto</ParticipantIndex>
    </Discovery>
  </Domain>
</CycloneDDS>
```

```bash
export CYCLONEDDS_URI=file:///path/to/cyclonedds.xml
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

- 给出验证步骤：

```bash
# 在容器 A 中
ros2 run demo_nodes_cpp talker

# 在容器 B 中
ros2 run demo_nodes_cpp listener
# 应能收到消息
```

## 案例 6：SLAM 建图飘移严重

### 输入问题

用户反馈：使用 Cartographer 或 SLAM Toolbox 建图时，地图出现明显扭曲、走廊重叠、回环失败，整体地图质量很差。

### skill 的处理路径

1. 加载 `references/slam-mapping.md`
2. 检查里程计质量：`ros2 topic hz /odom` 和数据连续性
3. 检查 TF 树完整性：`ros2 run tf2_tools view_frames`
4. 检查激光雷达数据质量：`ros2 topic echo /scan --once` 查看范围和噪声
5. 检查 IMU 是否正确融合（如果使用）

### 输出动作

- 里程计质量验证：

```bash
# 让机器人走一个正方形回到原点，检查里程计漂移量
ros2 topic echo /odom --field pose.pose.position
# 回到原点后 x, y 偏差应 < 5%
```

- 常见参数调优建议（以 SLAM Toolbox 为例）：

```yaml
slam_toolbox:
  ros__parameters:
    # 降低建图更新距离可提高精度但增加计算量
    minimum_travel_distance: 0.3    # 移动多少米更新一次
    minimum_travel_heading: 0.15    # 旋转多少弧度更新一次
    scan_buffer_size: 10
    resolution: 0.05
    max_laser_range: 20.0           # 根据雷达实际量程设置
```

- TF 配置检查要点：
  - 确认 `base_link -> laser_frame` 的外参准确
  - 确认里程计发布的 `odom -> base_link` 频率 >= 20Hz
  - 如果使用 IMU，确认 IMU 坐标系方向与 REP-105 一致
- 给出重新建图前的完整验证清单

## 案例 7：Lifecycle 节点状态转换失败

### 输入问题

用户反馈：Nav2 或自定义 lifecycle 节点卡在 `unconfigured` 或 `inactive` 状态，调用 `activate` 服务无响应或返回失败。

### skill 的处理路径

1. 加载 `references/lifecycle-and-components.md`
2. 检查节点当前状态
3. 检查回调函数实现是否正确返回 SUCCESS
4. 检查依赖服务或资源是否可用

### 输出动作

- 状态查询和转换命令：

```bash
# 查看节点当前生命周期状态
ros2 lifecycle get /节点名

# 查看可用的状态转换
ros2 lifecycle list /节点名

# 手动触发状态转换
ros2 lifecycle set /节点名 configure
ros2 lifecycle set /节点名 activate

# 如果卡住，查看节点日志
ros2 lifecycle set /节点名 configure --log-level debug
```

- 常见失败原因：
  - `on_configure()` 中加载参数文件失败（文件路径错或格式错）
  - `on_activate()` 中依赖的服务/topic 尚未就绪（启动顺序问题）
  - 回调函数抛出异常但未捕获，导致返回 `FAILURE`
  - 超时设置过短（特别是在硬件初始化时）
- 修复建议：
  - 在回调中添加异常捕获和详细日志
  - 使用 `launch_ros` 的 lifecycle 事件管理器控制启动顺序
  - 增大 `bond_timeout` 参数（Nav2 默认 10s）

## 案例 8：多机器人命名空间冲突

### 输入问题

用户反馈：同时启动两台相同配置的机器人后，topic 和 TF 互相干扰。一台机器人的导航指令会影响另一台，RViz 中两台机器人的模型重叠。

### skill 的处理路径

1. 加载 `references/multi-robot.md`
2. 检查 launch 文件中是否正确设置了命名空间
3. 检查 TF 是否有 frame prefix 隔离
4. 检查 DDS 配置和 `ROS_DOMAIN_ID`

### 输出动作

- 命名空间隔离方案（launch 文件）：

```python
from launch import LaunchDescription
from launch.actions import GroupAction
from launch_ros.actions import PushRosNamespace, Node

def generate_launch_description():
    robot1 = GroupAction([
        PushRosNamespace('robot1'),
        Node(package='my_robot', executable='driver',
             remappings=[('/tf', 'tf'), ('/tf_static', 'tf_static')]),
    ])
    robot2 = GroupAction([
        PushRosNamespace('robot2'),
        Node(package='my_robot', executable='driver',
             remappings=[('/tf', 'tf'), ('/tf_static', 'tf_static')]),
    ])
    return LaunchDescription([robot1, robot2])
```

- TF 隔离要点：
  - 每台机器人使用独立的 frame prefix（如 `robot1/base_link`, `robot2/base_link`）
  - 或使用独立的 TF topic（`/robot1/tf`, `/robot2/tf`）
  - 共享 `map` frame 但各自维护 `odom` frame
- 验证命令：

```bash
# 确认命名空间隔离生效
ros2 topic list | grep robot1
ros2 topic list | grep robot2

# 确认 TF 树独立
ros2 run tf2_tools view_frames
# 应看到两棵独立的 TF 树
```

- 给出完整的多机器人命名空间规划建议
