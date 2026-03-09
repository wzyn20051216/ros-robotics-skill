# 最小示例工作区 (Minimal Example Workspace)

本工作区是 `ros-robotics-skill` 项目的**最小可运行 ROS 2 示例**，演示了一个完整的 ROS 2 C++ 功能包的标准结构与最佳实践。

## 演示内容

| 组件 | 文件 | 说明 |
|------|------|------|
| 功能包描述 | `package.xml` | ament_cmake 构建系统、依赖声明 |
| 构建配置 | `CMakeLists.txt` | 编译目标、安装规则 |
| 发布者节点 | `src/talker.cpp` | 以 1Hz 向 `/chatter` 话题发布字符串消息 |
| 订阅者节点 | `src/listener.cpp` | 订阅 `/chatter` 并打印接收到的消息 |
| 启动文件 | `launch/demo.launch.py` | 同时启动 talker 和 listener 节点 |
| 参数文件 | `config/demo_params.yaml` | 配置 `message_prefix` 参数 |

## 先决条件

- **ROS 2 Humble** 或 **ROS 2 Jazzy**（推荐）
- `colcon` 构建工具
- `rosdep` 依赖管理工具

确认 ROS 2 环境已 source：

```bash
source /opt/ros/humble/setup.bash
# 或
source /opt/ros/jazzy/setup.bash
```

## 构建步骤

```bash
# 1. 进入工作区根目录
cd examples/minimal_ws

# 2. 安装依赖（首次构建时执行）
rosdep install --from-paths src --ignore-src -r -y

# 3. 编译工作区
colcon build --symlink-install

# 4. 加载工作区环境
source install/setup.bash
```

## 运行步骤

### 方式一：使用 launch 文件（推荐）

同时启动 talker 和 listener：

```bash
ros2 launch minimal_demo demo.launch.py
```

### 方式二：分别启动节点

打开终端 1（发布者）：

```bash
source install/setup.bash
ros2 run minimal_demo talker
```

打开终端 2（订阅者）：

```bash
source install/setup.bash
ros2 run minimal_demo listener
```

## 验证步骤

在另一个终端中，执行以下命令验证消息是否正常发布：

```bash
# 查看 /chatter 话题的实时消息
ros2 topic echo /chatter

# 查看话题列表
ros2 topic list

# 查看话题发布频率
ros2 topic hz /chatter

# 查看节点列表
ros2 node list
```

预期输出示例：

```
data: 'Hello from minimal_demo ROS 2 minimal demo - count: 42'
---
data: 'Hello from minimal_demo ROS 2 minimal demo - count: 43'
---
```

## 目录结构

```
minimal_ws/
├── README.md                          # 本文件
└── src/
    └── minimal_demo/
        ├── package.xml                # 功能包元信息与依赖
        ├── CMakeLists.txt             # CMake 构建配置
        ├── include/
        │   └── minimal_demo/
        │       └── talker.hpp         # TalkerNode 类声明
        ├── src/
        │   ├── talker.cpp             # 发布者节点实现
        │   └── listener.cpp           # 订阅者节点实现
        ├── launch/
        │   └── demo.launch.py         # 联合启动文件
        └── config/
            └── demo_params.yaml       # 节点参数配置
```

## 常见问题

**Q: colcon build 失败，提示找不到 rclcpp？**

A: 确保已正确 source ROS 2 环境：`source /opt/ros/humble/setup.bash`

**Q: rosdep install 失败？**

A: 首次使用需初始化 rosdep：`sudo rosdep init && rosdep update`

**Q: 节点启动后没有输出？**

A: 检查是否已 `source install/setup.bash`，或尝试添加 `--ros-args --log-level DEBUG`
