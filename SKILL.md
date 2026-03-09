---
name: ros-robotics
description: 适用于 ROS 1 与 ROS 2 机器人开发的 skill，覆盖 catkin/catkin_tools、colcon/ament、package.xml、CMakeLists.txt、launch、URDF/Xacro、RViz、TF、topic/service/action、导航感知联调，以及与 MCU 或 micro-ROS 的协同开发。
---

# ROS Robotics

## 概述

这个 skill 用于处理 **ROS 1 + ROS 2 + 机器人本体/驱动/算法/导航/嵌入式联调** 的开发任务。

它的目标不是强推某一种框架，而是先识别当前工作区和已有工程习惯，再选择 **最小改动、最可验证、最兼容** 的实现路线。

## 何时使用

当用户的请求涉及以下任一场景时使用本 skill：

- `catkin_ws`、`colcon_ws`、`src/CMakeLists.txt`、`package.xml`、`setup.py`
- ROS 1/ROS 2 package 新建、改造、移植、构建、测试、调试
- `launch` / `launch.py`、参数 YAML、URDF/Xacro、RViz、TF 树问题
- `topic` / `service` / `action` / `msg` / `srv` / `QoS` / `namespace` / `remap`
- 底盘、IMU、LiDAR、相机、串口、CAN、导航、定位、SLAM、仿真到实机联调
- MCU/RTOS 与 ROS 主机之间的桥接、串口协议、micro-ROS、时序与实时性问题

## 工作流决策

### 第一步：先识别工程类型

优先运行：

```bash
python scripts/detect_ros_workspace.py <workspace-path>
```

然后按结果读取对应参考文档：

- 检测到 `ros1-catkin`：读取 `references/ros1-catkin.md`
- 检测到 `ros2-colcon`：读取 `references/ros2-colcon.md`
- 检测到 `mixed`：读取 `references/interop-and-migration.md`
- 涉及 MCU/RTOS/串口/CAN/板端节点：额外读取 `references/micro-ros-and-embedded.md`
- 涉及审查、疑难问题或回归排查：读取 `references/review-checklist.md`

### 第二步：先收集上下文，再改代码

至少确认：

- ROS 大版本：ROS 1、ROS 2，还是混合系统
- 发行版与 OS：如 Noetic / Humble / Jazzy / Kilted，对应 Ubuntu 版本
- 工作区工具：`catkin_make`、`catkin_tools`、`colcon`
- 包类型：`catkin`、`ament_cmake`、`ament_python`
- 目标环境：仿真 / 实机 / Docker / 虚拟机 / 交叉编译
- 机器人链路：底盘、IMU、LiDAR、相机、串口、CAN、TF、导航栈
- 若连 MCU：MCU/SoC、RTOS、波特率/总线、时间基准、实时约束

如果这些信息不全，先从仓库内容、构建脚本、`package.xml`、`CMakeLists.txt`、`launch` 文件中推断；不要臆造接口。

## 核心原则

- **优先兼容现有工程**：先复用原有构建系统与目录布局，不要盲目迁移
- **优先 `rosdep`**：依赖问题先查 `package.xml` 与 `rosdep`
- **同时检查清单与构建脚本**：`package.xml` 与 `CMakeLists.txt` / `setup.py` 必须一致
- **先证据后修改**：topic 频率、TF、参数、时间戳、日志、构建输出要可验证
- **机器人问题优先排链路**：驱动 → 数据 → TF → 参数 → 算法 → 执行器
- **嵌入式问题优先排时序**：ISR、队列、时间戳、缓存、丢包、重连、看门狗
- **ROS 1/2 混合优先渐进式**：先桥接或分层，再谈全面迁移

## 常见任务处理方式

### 1. 新增或修复 package

- 先识别包是 ROS 1 还是 ROS 2，不要混写宏和构建逻辑
- 先对齐 `package.xml` 的依赖，再补 `CMakeLists.txt` / `setup.py`
- C++ 节点检查可执行目标、头文件导出、安装规则
- Python 节点检查入口、可执行权限、安装路径、依赖导出
- 自定义消息检查 `msg` / `srv` / `action` 生成链路与依赖顺序

### 2. 构建与测试

- 先 `rosdep install --from-paths src --ignore-src -r -y`
- ROS 1 保持项目原有 `catkin_make` 或 `catkin build`
- ROS 2 使用 `colcon build`、`colcon test`、`colcon test-result --verbose`
- 任何改动后都要跑最小可验证构建或目标包测试

### 3. 调试运行异常

- 先看 launch、参数、命名空间、remap 是否一致
- 再看 topic 名称、频率、时间戳、frame_id、消息单位是否一致
- 再看 TF 是否单根、时间是否连续、静态/动态变换是否放错
- ROS 2 额外检查 QoS 与参数声明；ROS 1 额外检查环境是否正确 source

### 4. 导航/感知/底层驱动联调

- 底盘：速度单位、坐标系方向、里程计积分、失连保护
- IMU：坐标轴定义、重力方向、角速度单位、时间同步、标定参数
- LiDAR：串口/USB 权限、雷达坐标系、扫描角度、时戳与 TF
- 导航：底盘约束、里程计质量、定位质量、代价地图参数、控制频率

### 5. MCU / micro-ROS 协同

- 如果 MCU 必须成为 ROS 2 图中的节点，再考虑 micro-ROS
- 如果只是传感器/底盘协议桥，很多场景下 Linux 侧桥接节点更简单稳妥
- 明确串口/CAN 帧格式、字节序、校验、超时、重传、时间源和失效保护
- 板端严控动态内存、阻塞调用、无界循环和 ISR 中的重活

## 输出要求

处理 ROS 任务时，优先输出：

1. 对当前工作区类型的判断
2. 变更点及原因
3. 最小构建/测试/运行命令
4. 关键风险点与回归检查点
5. 若涉及 ROS 1/ROS 2 兼容，说明兼容边界与不兼容项

## 参考文档导航

- `references/ros1-catkin.md`：ROS 1 `catkin` / `catkin_tools` 工作流
- `references/ros2-colcon.md`：ROS 2 `colcon` / `ament` 工作流
- `references/interop-and-migration.md`：ROS 1 ↔ ROS 2 桥接与迁移
- `references/micro-ros-and-embedded.md`：MCU、RTOS、micro-ROS、总线联调
- `references/review-checklist.md`：代码审查、回归与现场联调检查单


## ??????

????????? ROS ?????????

- `references/robot-description-and-tf.md`?URDF?Xacro?RViz?TF??????
- `references/navigation2.md`?Nav2?????????? `/cmd_vel` ??
- `references/ros2-control.md`?`ros2_control`???????????????? YAML
- `references/open-source-publishing.md`??? GitHub ?????????

## ????

? `scripts/detect_ros_workspace.py` ???????

```bash
python scripts/check_ros_workspace_consistency.py <workspace-path>
```

???????

- `package.xml` ????? `CMakeLists.txt` ??????
- ROS 2 ??????? `launch/`?`config/`?`urdf/`?`rviz/` ?????
- ??????????????
