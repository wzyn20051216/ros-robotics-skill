# ROS 2 Colcon 工作流

## 适用场景

当工作区或包具备以下特征时使用本参考：

- 包内出现 `ament_cmake`、`ament_python`、`ament_package()`
- 工作区使用 `colcon build`
- 存在 `install/`、`log/`、`colcon.meta`
- 启动文件以 `launch.py` 为主，且任务涉及 QoS、Lifecycle、参数声明等 ROS 2 特性

## 安全默认流程

### 1. 准备环境

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
rosdep install --from-paths src --ignore-src -r -y
```

### 2. 构建与测试

```bash
colcon build
source install/setup.bash
colcon test
colcon test-result --verbose
```

根据 ROS 2 官方教程，`colcon build`、`colcon test` 与 `colcon test-result --verbose` 是标准构建/测试路径。

## 修改 package 时的重点

### 1. 包类型要分清

- C++ 包通常为 `ament_cmake`
- Python 包通常为 `ament_python`
- 不要把 ROS 1 `catkin` 宏塞进 ROS 2 包里

### 2. `package.xml`

- 优先保持 `format="3"`
- 依赖声明要覆盖构建、运行、测试三类场景
- 若涉及跨版本兼容，优先用条件依赖，不要先分叉多个几乎相同的包

### 3. `CMakeLists.txt` / `setup.py`

- `ament_package()` 要保留在正确位置
- 可执行目标、安装规则、头文件、配置文件、launch、URDF/Xacro 需要显式安装
- Python 包要检查入口点、依赖导出、资源文件安装路径

### 4. QoS / 参数 / 生命周期

- 传感器话题不要默认假设 QoS 一样
- 参数通常需要声明，检查默认值、单位、范围与 launch 覆盖关系
- Lifecycle node 相关改动要验证状态迁移与错误恢复路径

## 常见调试路径

```bash
ros2 topic list
ros2 topic info /topic_name
ros2 node list
ros2 node info /node_name
ros2 param list
ros2 doctor
```

优先检查：

- QoS 是否匹配
- 参数是否声明且生效
- namespace / remap 是否正确
- 时钟是否使用 `/use_sim_time`
- TF、时间戳、消息单位是否一致

## 审查重点

- 是否遗漏 `install(...)` 导致 launch/配置文件运行时找不到
- 是否遗漏测试依赖或测试命令
- 是否将 ROS 1 launch 机械翻译为 ROS 2 launch 而未验证命名空间/QoS
- 是否把硬件访问、业务逻辑、状态机、诊断全揉在单节点里

## 官方参考

- ROS 2 `colcon` 教程：<https://docs.ros.org/en/kilted/Tutorials/Beginner-Client-Libraries/Colcon-Tutorial.html>
- `rosdep` 文档：<https://docs.ros.org/en/kilted/Tutorials/Intermediate/Rosdep.html>
- `package.xml` 条件依赖（REP-149）：<https://www.ros.org/reps/rep-0149.html>
- ROS 2 质量与 Lint：<https://docs.ros.org/en/rolling/Tutorials/Advanced/Ament-Lint-For-Clean-Code.html>
