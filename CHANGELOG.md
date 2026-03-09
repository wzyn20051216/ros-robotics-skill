# Changelog

## 0.4.0 - 2026-03-09

### 新增

- 新增 `examples/minimal_ws/`：最小示例工作区，含 C++ talker/listener 节点、CMakeLists.txt、launch 文件、参数 YAML，可直接 `colcon build` 运行
- 新增 `references/foxglove-visualization.md`：Foxglove Studio / PlotJuggler 数据可视化（工具对比、连接配置、常用面板、调试工作流、常见问题）

### 更新

- 更新 `SKILL.md`、`README.md`：新增 Foxglove 触发条件和文档索引，Roadmap 全部完成
- 版本升级至 `0.4.0`

## 0.3.0 - 2026-03-09

### 新增参考文档

- 新增 `references/gazebo-simulation.md`：Gazebo 仿真集成（Classic vs Gz、传感器配置、ros_gz_bridge、launch 集成）
- 新增 `references/lifecycle-and-components.md`：Lifecycle 节点与组件化（状态转换、rclcpp_components、容器化运行）
- 新增 `references/dds-qos-networking.md`：DDS / QoS / 网络配置（RMW 选择、QoS Profile、多机网络、Discovery Server）
- 新增 `references/rosbag-diagnostics.md`：rosbag2 录制回放与诊断（mcap 格式、离线调试工作流）
- 新增 `references/slam-mapping.md`：SLAM 建图与定位（Cartographer、SLAM Toolbox、地图管理、IMU 融合）
- 新增 `references/docker-ros.md`：Docker 容器化 ROS 开发（多阶段构建、GUI 转发、docker-compose 编排）
- 新增 `references/custom-interfaces.md`：自定义 msg/srv/action（语法、包结构、CMake 配置、版本兼容）
- 新增 `references/multi-robot.md`：多机器人系统（命名空间隔离、TF 隔离、跨机通信、时间同步）

### 加深现有文档

- 加深 `references/navigation2.md`：补充 Nav2 参数调优模板、Costmap 配置示例、AMCL 验证、/cmd_vel 链路调试
- 加深 `references/ros2-control.md`：补充控制器 YAML 配置模板、硬件接口 URDF 示例、调试命令
- 加深 `references/debug-playbooks.md`：新增 4 个高级 Playbook（TF 断裂、参数失效、launch 部分失败、性能异常）

### 案例与脚本

- 扩充 `examples/case-studies.md`：新增 5 个高级案例（QoS 丢帧、Docker 节点发现、SLAM 飘移、Lifecycle 失败、多机器人冲突）
- 新增 `scripts/check_tf_tree.py`：URDF/Xacro TF 树完整性离线检查（单根性、悬挂 link、重复名称、循环依赖）

### 新增 MoveIt 2 与 CI/CD

- 新增 `references/moveit2.md`：MoveIt 2 运动规划（SRDF、运动学插件、规划器配置、C++ API、Gazebo 联合仿真）
- 新增 `references/ros2-cicd.md`：ROS 2 CI/CD 最佳实践（GitHub Actions 模板、ament_lint、覆盖率、多平台 CI）

### 增强工具

- 增强 `scripts/check_ros_workspace_consistency.py`：深度 CMake 分析（target_link_libraries / install(TARGETS) / ament_target_dependencies）、package.xml 冗余检查、launch 文件引用检查、YAML 语法检查、扩展资源目录检查（maps/worlds/models/meshes）

### 更新

- 更新 `SKILL.md`：新增 Gazebo、Docker、Lifecycle、rosbag、SLAM、QoS、自定义接口、多机器人、MoveIt 2、CI/CD 触发条件和文档索引
- 更新 `README.md`：核心能力扩展至 19 项、20 个参考文档、Roadmap 更新，新增 Star 引导
- 版本升级至 `0.3.0`

## 0.2.1 - 2026-03-09

- 修复 Windows GitHub Actions 编码问题
- 修复 Windows CI 下关键文件检查脚本的跨平台兼容性
- 将 `npx skills add` 提升为 README 首屏安装方式
- 重写 README 首屏，补充 Windows PowerShell 一键安装入口
- 使用 GitHub 原生支持的 Mermaid 流程图替代损坏图片链接
- 新增 `scripts/validate_project.py` 用于跨平台关键文件校验

## 0.2.0 - 2026-03-09

- 补齐 `URDF/Xacro/TF`、`Navigation2`、`ros2_control` 三个高频 ROS 专题
- 新增 `README`、`docs/INSTALL.md`、`docs/COMPATIBILITY.md` 等开源项目文档
- 新增一键安装脚本：`install.sh`、`install.ps1`、`scripts/install.py`
- 新增 Gemini CLI 命令适配：`integrations/gemini/commands/ros-robotics.md`
- 新增自动化测试与 GitHub Actions CI
- 新增真实案例、社区模板与贡献说明

## 0.1.0 - 2026-03-09

- 初始化 `ros-robotics` skill
- 提供 ROS 1 / ROS 2 / 迁移 / 嵌入式联调基础文档
- 提供工作区识别脚本 `detect_ros_workspace.py`
