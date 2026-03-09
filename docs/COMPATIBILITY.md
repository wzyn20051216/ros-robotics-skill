# 兼容矩阵

## ROS / Ubuntu

| 维度 | 状态 | 说明 |
| --- | --- | --- |
| ROS 1 Noetic | 支持 | 重点覆盖 `catkin_make` / `catkin build` |
| ROS 2 Humble | 支持 | 重点覆盖 `colcon` / `ament` / Nav2 / `ros2_control` |
| ROS 2 Jazzy | 支持 | 文档与工作流适配 |
| ROS 2 Rolling | 部分支持 | 优先参考官方文档验证 API 变化 |
| Ubuntu 20.04 | 支持 | 适合 ROS 1 Noetic / ROS 2 Humble 混合环境 |
| Ubuntu 22.04 | 支持 | 适合 ROS 2 Humble / Jazzy |
| Ubuntu 24.04 | 部分支持 | ROS 1 与 `ros1_bridge` 组合受限 |

## 主机集成

| Host | 状态 | 说明 |
| --- | --- | --- |
| Codex | 支持 | 原生 skill 目录安装 |
| Claude Code | 支持 | 原生 skill 目录安装 |
| Gemini CLI | 支持 | 通过命令包安装等价工作流 |
