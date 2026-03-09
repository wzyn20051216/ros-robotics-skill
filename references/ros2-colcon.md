# ROS 2 Colcon 工作流

## 适用场景

- 包使用 `ament_cmake` 或 `ament_python`
- 工作区使用 `colcon build`
- 任务涉及 QoS、参数声明、Lifecycle 或安装规则

## 安全默认流程

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build
source install/setup.bash
colcon test
colcon test-result --verbose
```

## 核心检查点

- `package.xml format="3"` 依赖是否完整
- `ament_package()` 是否保留在正确位置
- `launch/`、`config/`、`urdf/`、`rviz/` 是否有安装规则
- QoS、参数声明、命名空间、`use_sim_time` 是否处理正确

## 常见调试命令

```bash
ros2 topic list
ros2 topic info /topic_name
ros2 node list
ros2 node info /node_name
ros2 param list
ros2 doctor
```

## 官方参考

- ROS 2 `colcon`：<https://docs.ros.org/en/kilted/Tutorials/Beginner-Client-Libraries/Colcon-Tutorial.html>
- `rosdep`：<https://docs.ros.org/en/kilted/Tutorials/Intermediate/Rosdep.html>
- REP-149：<https://www.ros.org/reps/rep-0149.html>
