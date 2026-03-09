# ROS Robotics Skill

![CI](https://github.com/wzyn20051216/ros-robotics-skill/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/github/license/wzyn20051216/ros-robotics-skill)
![Stars](https://img.shields.io/github/stars/wzyn20051216/ros-robotics-skill?style=social)

一个面向 **ROS 1 / ROS 2 机器人开发、迁移与联调** 的开源工程化 skill / prompt pack，适配 **Codex、Claude Code、Gemini CLI**。

英文版见：[README.en.md](README.en.md)

## 它到底解决什么问题

大多数通用 AI 提示词在 ROS 项目里有 4 个通病：

- 分不清 `catkin` 和 `ament`
- 看见问题先改代码，不先排 TF、时间戳、frame、单位和资源安装
- 不知道 Nav2、`ros2_control`、底盘反馈、`/cmd_vel` 的联调顺序
- 看见 MCU 就想上 `micro-ROS`，不会先判断 Linux 侧桥接是否更简单

这个项目就是专门解决这些问题的。

## 支持哪些主机

| Host | 集成方式 | 安装位置 |
| --- | --- | --- |
| Codex | 原生 skill | `~/.codex/skills/ros-robotics` |
| Claude Code | 原生 skill | `~/.claude/skills/ros-robotics` |
| Gemini CLI | 命令包 | `~/.gemini/commands/ros-robotics.md` |

> 说明：Gemini CLI 当前没有与 `SKILL.md` 完全等价的原生 skill 目录机制，所以这里提供的是 **等价工作流命令包**。

## Skills CLI 安装（推荐给习惯 `npx skills` 的用户）

如果你已经在用 Skills CLI，可以直接从 GitHub 安装：

```bash
npx skills add https://github.com/wzyn20051216/ros-robotics-skill -g -y
```

如果你更喜欢仓库简称，也可以试试：

```bash
npx skills add wzyn20051216/ros-robotics-skill -g -y
```

> 说明：不同环境对 GitHub HTTPS/代理策略不一样，若简称失败，优先使用完整 URL。

## 一条命令安装

### Linux / macOS

自动识别并安装到可用主机：

```bash
curl -fsSL https://raw.githubusercontent.com/wzyn20051216/ros-robotics-skill/main/install.sh | bash
```

显式指定目标：

```bash
curl -fsSL https://raw.githubusercontent.com/wzyn20051216/ros-robotics-skill/main/install.sh | bash -s -- --target codex
curl -fsSL https://raw.githubusercontent.com/wzyn20051216/ros-robotics-skill/main/install.sh | bash -s -- --target claude
curl -fsSL https://raw.githubusercontent.com/wzyn20051216/ros-robotics-skill/main/install.sh | bash -s -- --target gemini
```

### Windows PowerShell

自动识别并安装到可用主机：

```powershell
irm https://raw.githubusercontent.com/wzyn20051216/ros-robotics-skill/main/install.ps1 | iex
```

显式指定目标：

```powershell
$env:ROS_ROBOTICS_TARGET='codex'; irm https://raw.githubusercontent.com/wzyn20051216/ros-robotics-skill/main/install.ps1 | iex
$env:ROS_ROBOTICS_TARGET='claude'; irm https://raw.githubusercontent.com/wzyn20051216/ros-robotics-skill/main/install.ps1 | iex
$env:ROS_ROBOTICS_TARGET='gemini'; irm https://raw.githubusercontent.com/wzyn20051216/ros-robotics-skill/main/install.ps1 | iex
```

### 本地源码安装

```bash
git clone https://github.com/wzyn20051216/ros-robotics-skill.git
cd ros-robotics-skill
python scripts/install.py --target all --force
```

### 卸载

```bash
python scripts/install.py --target codex --uninstall
python scripts/install.py --target claude --uninstall
python scripts/install.py --target gemini --uninstall
```

## 工作流总览

```mermaid
flowchart LR
    A[识别工作区
ROS1 / ROS2 / mixed] --> B[检查 package.xml
CMakeLists.txt / install 规则]
    B --> C[按专题加载文档
TF / URDF / Nav2 / ros2_control / MCU]
    C --> D[小步修改]
    D --> E[最小验证
构建 / 运行 / 回归]
```

## 核心能力

- `ROS 1 / ROS 2 / mixed workspace` 识别与处理
- `catkin_make`、`catkin build`、`colcon build` 工作流
- `package.xml` / `CMakeLists.txt` / 资源安装规则一致性检查
- `URDF/Xacro`、`robot_state_publisher`、RViz、TF 树调试
- Navigation2 参数调优、Costmap 配置、定位与导航联调
- `ros2_control` 硬件接口、控制器 YAML、读写周期问题定位
- Gazebo / Ignition 仿真集成、传感器配置、`ros_gz_bridge`
- Lifecycle 节点与 `rclcpp_components` 组件化
- DDS / QoS 配置、多机网络、RMW 选择
- `rosbag2` 录制回放、`mcap`、离线诊断工作流
- SLAM 建图（Cartographer、SLAM Toolbox）与定位
- Docker 容器化 ROS 开发与多节点编排
- 自定义 `msg` / `srv` / `action` 接口定义
- 多机器人系统命名空间隔离与跨机通信
- MCU / RTOS / 串口 / CAN / `micro-ROS` 协同开发与风险审查
- ROS 1 → ROS 2 渐进迁移建议
- TF 树完整性离线检查（URDF/Xacro 解析）

## 项目结构

```text
.
├── SKILL.md
├── agents/
├── docs/
├── examples/
├── integrations/
│   └── gemini/
├── references/          # 18 个专题参考文档
├── scripts/             # 工作区检测、一致性检查、TF 树检查
├── tests/
└── .github/
```

## 5 分钟上手

### 1. 识别工作区

```bash
python scripts/detect_ros_workspace.py /path/to/workspace
```

### 2. 检查依赖与安装规则

```bash
python scripts/check_ros_workspace_consistency.py /path/to/workspace
```

### 3. 按专题加载参考文档

- ROS 1：`references/ros1-catkin.md`
- ROS 2：`references/ros2-colcon.md`
- 迁移：`references/interop-and-migration.md`
- 模型 / TF：`references/robot-description-and-tf.md`
- 导航：`references/navigation2.md`
- 控制：`references/ros2-control.md`
- 嵌入式：`references/micro-ros-and-embedded.md`
- 仿真：`references/gazebo-simulation.md`
- Lifecycle / 组件：`references/lifecycle-and-components.md`
- DDS / QoS / 网络：`references/dds-qos-networking.md`
- 录制回放：`references/rosbag-diagnostics.md`
- SLAM：`references/slam-mapping.md`
- Docker：`references/docker-ros.md`
- 自定义接口：`references/custom-interfaces.md`
- 多机器人：`references/multi-robot.md`

## 真实案例

见：`examples/case-studies.md`

## 文档

- 安装说明：`docs/INSTALL.md`
- 兼容矩阵：`docs/COMPATIBILITY.md`
- 贡献指南：`CONTRIBUTING.md`
- 变更记录：`CHANGELOG.md`

## 官方资料来源

- ROS 1 `catkin`：<https://docs.ros.org/en/noetic/api/catkin/html/>
- `catkin_tools`：<https://catkin-tools.readthedocs.io/en/latest/quick_start.html>
- ROS 2 `colcon`：<https://docs.ros.org/en/kilted/Tutorials/Beginner-Client-Libraries/Colcon-Tutorial.html>
- `rosdep`：<https://docs.ros.org/en/kilted/Tutorials/Intermediate/Rosdep.html>
- `ros1_bridge`：<https://docs.ros.org/en/humble/p/ros1_bridge/>
- `xacro`：<https://docs.ros.org/en/ros2_packages/jazzy/api/xacro/>
- Nav2：<https://docs.nav2.org/getting_started/>
- `ros2_control`：<https://control.ros.org/master/doc/getting_started/getting_started.html>
- micro-ROS：<https://micro.ros.org/docs/overview/introduction/>
- Gemini CLI custom commands：<https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/commands.md>

## Roadmap

- [x] ROS 1 / ROS 2 / mixed workspace 检测
- [x] TF / URDF / Nav2 / `ros2_control` / `micro-ROS` 参考文档
- [x] Codex / Claude / Gemini 安装器
- [x] 测试与 CI
- [x] 英文 README
- [x] Gazebo / Docker / Lifecycle / rosbag / SLAM / DDS·QoS / 自定义接口 / 多机器人参考文档
- [x] Nav2 参数调优模板与 Costmap 配置示例
- [x] `ros2_control` 控制器 YAML 配置模板
- [x] 高级排障 Playbook（TF 断裂、参数失效、launch 部分失败、性能异常）
- [x] 8 个真实案例覆盖 QoS / Docker / SLAM / Lifecycle / 多机器人
- [x] TF 树完整性离线检查脚本
- [ ] 最小示例工作区
- [ ] 更强的依赖 / 资源安装规则检查器
- [ ] MoveIt 2 运动规划参考文档
- [ ] ROS 2 CI/CD 最佳实践（GitHub Actions + colcon test）
- [ ] Foxglove / PlotJuggler 数据可视化参考

> 如果你觉得这个项目有用，欢迎给个 ⭐ Star 支持一下！
