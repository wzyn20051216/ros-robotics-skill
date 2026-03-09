# ROS Robotics Skill

![CI](https://github.com/wzyn20051216/ros-robotics-skill/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/github/license/wzyn20051216/ros-robotics-skill)
![Stars](https://img.shields.io/github/stars/wzyn20051216/ros-robotics-skill?style=social)

一个面向 **ROS 1 / ROS 2 机器人开发、迁移与联调** 的开源工程化 skill / prompt pack。

> English summary: see `README.en.md`

![workflow](docs/images/ros-robotics-flow.svg)

它不是“ROS 关键词词典”，而是一套面向真实机器人项目的工作流：

- 先识别工作区和构建系统
- 再定位 `package.xml`、`CMakeLists.txt`、`launch`、`TF`、`URDF/Xacro`、Nav2、`ros2_control`、MCU / `micro-ROS` 链路问题
- 最后给出 **最小可验证修改** 和 **最小回归命令**

## Why this project

多数通用 AI 提示词在 ROS 场景里有几个典型问题：

- 分不清 `catkin` 和 `ament`
- 只会改代码，不会先排查 TF、时间戳、坐标系、单位和资源安装
- 看见 `micro-ROS` 就乱上，不会先判断 Linux 侧桥接是否更合理
- 不知道 Nav2 和 `ros2_control` 的联调顺序

这个项目就是为了解决这些问题。

## 支持范围

| Host | 集成方式 | 安装位置 |
| --- | --- | --- |
| Codex | 原生 skill | `~/.codex/skills/ros-robotics` |
| Claude Code | 原生 skill | `~/.claude/skills/ros-robotics` |
| Gemini CLI | 自定义命令包 | `~/.gemini/commands/ros-robotics.md` |

> 说明：Gemini CLI 当前采用原生命令扩展而不是 `SKILL.md` 目录结构，因此这里提供的是 **等价工作流命令包**。

## 一键安装

### Linux / macOS

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

```powershell
irm https://raw.githubusercontent.com/wzyn20051216/ros-robotics-skill/main/install.ps1 | iex
```

显式指定目标：

```powershell
$env:ROS_ROBOTICS_TARGET='codex'; irm https://raw.githubusercontent.com/wzyn20051216/ros-robotics-skill/main/install.ps1 | iex
$env:ROS_ROBOTICS_TARGET='claude'; irm https://raw.githubusercontent.com/wzyn20051216/ros-robotics-skill/main/install.ps1 | iex
$env:ROS_ROBOTICS_TARGET='gemini'; irm https://raw.githubusercontent.com/wzyn20051216/ros-robotics-skill/main/install.ps1 | iex
```

## 卸载

```bash
python scripts/install.py --target codex --uninstall
python scripts/install.py --target claude --uninstall
python scripts/install.py --target gemini --uninstall
```

## 核心能力

- `ROS 1 / ROS 2 / mixed workspace` 识别与处理
- `catkin_make`、`catkin build`、`colcon build` 工作流
- `package.xml` / `CMakeLists.txt` / 资源安装规则一致性检查
- `URDF/Xacro`、`robot_state_publisher`、RViz、TF 树调试
- Navigation2、`/cmd_vel` 控制链路、定位与导航联调
- `ros2_control` 硬件接口、控制器 YAML、读写周期问题定位
- MCU / RTOS / 串口 / CAN / `micro-ROS` 协同开发与风险审查
- ROS 1 → ROS 2 渐进迁移建议

## 项目结构

```text
.
├── SKILL.md
├── agents/
├── docs/
├── examples/
├── integrations/
│   └── gemini/
├── references/
├── scripts/
├── tests/
└── .github/
```

## 快速上手

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
- [x] 英文摘要与 README.en
- [ ] 最小示例工作区
- [ ] 更强的依赖 / 资源安装规则检查器
