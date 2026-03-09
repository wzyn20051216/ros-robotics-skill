# ROS 1 Catkin 工作流

## 适用场景

当工作区或包具备以下特征时使用本参考：

- 根目录存在 `src/CMakeLists.txt`
- 包内 `CMakeLists.txt` 使用 `find_package(catkin REQUIRED ...)`
- `package.xml` 中 `buildtool_depend` 为 `catkin`
- 工作区中出现 `devel/`、`.catkin_tools/` 或历史命令明显属于 ROS 1

## 安全默认流程

### 1. 准备环境

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
rosdep install --from-paths src --ignore-src -r -y
```

说明：`rosdep` 用于按 `package.xml` 安装系统依赖，不要手工东补一个包西补一个包。

### 2. 选择构建工具

- 如果项目已经在用 `catkin_tools`，优先继续用 `catkin build`
- 如果项目一直在用 `catkin_make`，优先保持不变
- 不要在同一个历史项目里随意切换构建工具，除非先清理构建产物并验证脚本/CI

常用命令：

```bash
catkin build
# 或
catkin_make
source devel/setup.bash
```

根据 `catkin_tools` Quickstart，`catkin init` 用于初始化工作区，`catkin build` 用于按包构建；已有工程优先沿用现状。

## 修改 package 时的重点

### 1. `package.xml`

- 依赖必须完整声明：构建依赖、导出依赖、运行依赖要区分清楚
- 新增节点、消息、动态重配置时，依赖同步补齐
- 不要只改 `CMakeLists.txt` 不改 `package.xml`

### 2. `CMakeLists.txt`

- `find_package(catkin REQUIRED COMPONENTS ...)` 要与真实依赖一致
- `catkin_package(...)` 的导出项要与头文件/库实际情况一致
- `include_directories(...)`、`target_link_libraries(...)`、`add_dependencies(...)` 要闭环
- 如果有 `msg` / `srv` / `action`，检查生成顺序与 message 依赖
- Python 脚本要注意安装或可执行权限，避免“能运行但不能发布”

### 3. `launch` / 参数 / TF

- `launch` 中的 node 名称、namespace、remap 要和代码一致
- YAML 参数路径、默认值和读取时机要对应
- `frame_id`、`child_frame_id`、单位、坐标轴方向要统一
- 机器人问题优先排 TF 树与时间戳，再排算法本身

## 常见调试路径

```bash
rostopic list
rostopic hz /topic_name
rosnode list
rosnode info /node_name
rosparam get /param_name
```

优先检查：

- 话题是否存在
- 频率是否正常
- 时间戳是否连续
- `frame_id` 是否正确
- launch 是否漏 source、漏参数、漏 remap

## 审查重点

- 是否误把 ROS 1 包按 ROS 2 方式修改
- 是否遗漏 `package.xml` 依赖
- 是否在多个 launch 中复制粘贴了冲突参数
- 是否把设备节点、协议解析、滤波、控制耦合在一个大节点里
- 是否缺少失连保护、超时保护、串口异常处理

## 官方参考

- ROS 1 `catkin` 文档：<https://docs.ros.org/en/noetic/api/catkin/html/>
- `catkin_tools` Quickstart：<https://catkin-tools.readthedocs.io/en/latest/quick_start.html>
- `rosdep` 文档：<https://docs.ros.org/en/kilted/Tutorials/Intermediate/Rosdep.html>
