# ROS 1 Catkin 工作流

## 适用场景

- 工作区存在 `src/CMakeLists.txt`
- 包使用 `find_package(catkin REQUIRED ...)`
- `package.xml` 中 `buildtool_depend` 为 `catkin`

## 安全默认流程

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
rosdep install --from-paths src --ignore-src -r -y
catkin build    # 若项目使用 catkin_tools
catkin_make     # 若项目历史上使用 catkin_make
source devel/setup.bash
```

## 核心检查点

- `package.xml`、`CMakeLists.txt` 是否同步
- `find_package(catkin REQUIRED COMPONENTS ...)` 是否完整
- `catkin_package(...)`、`target_link_libraries(...)`、`add_dependencies(...)` 是否闭环
- `launch`、参数 YAML、TF、`frame_id` 是否一致

## 常见调试命令

```bash
rostopic list
rostopic hz /topic_name
rosnode list
rosnode info /node_name
rosparam get /param_name
```

## 官方参考

- ROS 1 `catkin`：<https://docs.ros.org/en/noetic/api/catkin/html/>
- `catkin_tools`：<https://catkin-tools.readthedocs.io/en/latest/quick_start.html>
