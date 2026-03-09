# ros2_control 联调参考

## 第一原则

`ros2_control` 问题通常出在 **硬件接口导出、控制器配置、接口类型匹配、读写周期**，而不是先怪控制器本身。

## 检查顺序

1. 硬件组件是 `system`、`sensor` 还是 `actuator`
2. 导出的接口类型是否正确：`position` / `velocity` / `effort`
3. 控制器 YAML 是否与硬件导出的接口一致
4. 控制器是否真正进入 active 状态
5. 硬件读写周期是否稳定

## 控制器 YAML 配置模板

以下是差速驱动机器人的典型 `ros2_controllers.yaml` 配置：

```yaml
controller_manager:
  ros__parameters:
    update_rate: 50                     # 控制器更新频率 Hz
    use_sim_time: false

    # 声明控制器
    joint_state_broadcaster:
      type: joint_state_broadcaster/JointStateBroadcaster

    diff_drive_controller:
      type: diff_drive_controller/DiffDriveController

joint_state_broadcaster:
  ros__parameters:
    # 通常无需额外参数，自动广播所有关节状态
    publish_rate: 50.0                  # 状态发布频率

diff_drive_controller:
  ros__parameters:
    publish_rate: 50.0
    base_frame_id: base_link
    odom_frame_id: odom

    # 左右轮关节名称，必须与 URDF 中定义一致
    left_wheel_names: ["left_wheel_joint"]
    right_wheel_names: ["right_wheel_joint"]

    # 机器人物理参数 — 务必精确测量
    wheel_separation: 0.34              # 轮距 m
    wheel_radius: 0.05                  # 轮半径 m

    # 里程计倍率校正（实测校准用）
    wheel_separation_multiplier: 1.0
    left_wheel_radius_multiplier: 1.0
    right_wheel_radius_multiplier: 1.0

    # 发布 odom->base_link TF
    enable_odom_tf: true

    # 速度限制
    linear.x.has_velocity_limits: true
    linear.x.max_velocity: 0.5         # m/s
    linear.x.min_velocity: -0.3
    linear.x.has_acceleration_limits: true
    linear.x.max_acceleration: 1.0
    angular.z.has_velocity_limits: true
    angular.z.max_velocity: 1.5        # rad/s
    angular.z.min_velocity: -1.5

    # 指令超时保护
    cmd_vel_timeout: 0.5               # 超时未收到命令则停止
```

## 硬件接口 URDF 配置示例

在 URDF/xacro 中通过 `<ros2_control>` 标签声明硬件接口：

```xml
<ros2_control name="RobotSystem" type="system">
  <hardware>
    <!-- 仿真用 GazeboSystem，实物替换为自定义插件 -->
    <plugin>gazebo_ros2_control/GazeboSystem</plugin>
    <!-- 实物示例：
    <plugin>my_robot_hardware/MyRobotHardwareInterface</plugin>
    <param name="serial_port">/dev/ttyUSB0</param>
    <param name="baud_rate">115200</param>
    -->
  </hardware>

  <joint name="left_wheel_joint">
    <command_interface name="velocity">
      <param name="min">-10.0</param>
      <param name="max">10.0</param>
    </command_interface>
    <state_interface name="position"/>
    <state_interface name="velocity"/>
  </joint>

  <joint name="right_wheel_joint">
    <command_interface name="velocity">
      <param name="min">-10.0</param>
      <param name="max">10.0</param>
    </command_interface>
    <state_interface name="position"/>
    <state_interface name="velocity"/>
  </joint>
</ros2_control>
```

关键要点：
- `command_interface` 的 `name` 决定控制器可以写入的接口类型
- `state_interface` 的 `name` 决定控制器可以读取的反馈类型
- 关节名称必须与 URDF `<joint>` 标签中的 `name` 完全一致
- `type="system"` 表示多关节耦合，适用于差速/麦轮底盘

## 调试命令

```bash
# 1. 列出所有硬件接口（确认硬件插件加载成功）
ros2 control list_hardware_interfaces
# 应看到每个关节的 command_interface 和 state_interface
# 状态为 [available] 表示可用，[claimed] 表示已被控制器占用

# 2. 列出所有控制器及其状态
ros2 control list_controllers
# 期望看到：active / inactive / unconfigured

# 3. 手动加载控制器
ros2 control load_controller diff_drive_controller

# 4. 配置控制器（从 unconfigured -> inactive）
ros2 control set_controller_state diff_drive_controller configure

# 5. 激活控制器（从 inactive -> active）
ros2 control set_controller_state diff_drive_controller activate

# 6. 停用控制器
ros2 control set_controller_state diff_drive_controller deactivate

# 7. 卸载控制器
ros2 control unload_controller diff_drive_controller

# 8. 切换控制器（原子操作，同时停用旧的、激活新的）
ros2 control switch_controllers \
  --activate new_controller \
  --deactivate old_controller
```

## 状态监控

```bash
# 检查 joint_state 是否正常发布
ros2 topic echo /joint_states

# 检查发布频率（应接近 controller_manager 的 update_rate）
ros2 topic hz /joint_states

# 检查 controller_manager 节点的参数
ros2 param list /controller_manager

# 查看具体控制器参数
ros2 param get /diff_drive_controller wheel_separation

# 检查 odom 输出是否合理
ros2 topic echo /diff_drive_controller/odom

# 检查 controller_manager 日志（查找加载/激活错误）
ros2 node info /controller_manager
```

## 常见故障

### 控制器加载失败

- 硬件插件名错
- 参数文件路径错
- 接口类型不匹配
- 依赖包未正确安装

### 控制器启动但机器人不动

- 写接口未真正下发到底层
- 底层驱动忽略了控制量
- 状态反馈频率过低
- 速度 / 位置 / 力矩语义混乱

### 硬件接口注册失败

- URDF 中 `<ros2_control>` 标签的 `plugin` 名称拼写错误或包未安装
- 硬件插件的 `on_init()` 返回了 `ERROR`（检查串口/总线连接）
- `export_state_interfaces()` 或 `export_command_interfaces()` 返回的接口数量与 URDF 声明不一致
- 排查：查看 `controller_manager` 启动时的完整日志输出
- 修复：确认插件名、检查物理连接、对比 URDF 声明和代码中的接口导出

### 控制器 claim 接口冲突

- 两个控制器试图 claim 同一个 `command_interface`（如两个都要写 `velocity`）
- 排查：`ros2 control list_hardware_interfaces` 看哪些接口被 `[claimed]`
- 修复：同一时刻只激活一个写同类接口的控制器，使用 `switch_controllers` 原子切换

### 更新频率不匹配

- `controller_manager` 的 `update_rate` 与硬件实际读写能力不匹配
- 症状：`controller_manager` 日志报 `cycle time exceeded` 或实际频率远低于设定值
- 硬件 `read()` / `write()` 阻塞时间过长（串口超时、总线拥堵）
- 排查：用 `ros2 topic hz /joint_states` 验证实际频率
- 修复：降低 `update_rate` 或优化硬件通信（DMA、异步读写、增大缓冲区）

### 关节名称不一致

- URDF 中 `<joint name="xxx">` 与控制器 YAML 中的关节名不匹配
- 症状：控制器加载成功但找不到接口
- 排查：对比 URDF 和 YAML 中的关节名，注意大小写和下划线
- 修复：统一命名，建议使用 xacro 变量避免拼写不一致

## 官方与高星参考

- `ros2_control` Getting Started：<https://control.ros.org/master/doc/getting_started/getting_started.html>
- `ros2_controllers`：<https://control.ros.org/humble/doc/ros2_controllers/doc/controllers_index.html>
- `ros2_control` GitHub：<https://github.com/ros-controls/ros2_control>
- `ros2_control` 架构概述：<https://control.ros.org/master/doc/ros2_control/doc/index.html>
- diff_drive_controller 文档：<https://control.ros.org/humble/doc/ros2_controllers/diff_drive_controller/doc/userdoc.html>
- 硬件接口开发指南：<https://control.ros.org/master/doc/ros2_control/hardware_interface/doc/writing_new_hardware_component.html>
- `gazebo_ros2_control`：<https://github.com/ros-controls/gazebo_ros2_control>
- ros2_control 示例仓库：<https://github.com/ros-controls/ros2_control_demos>
