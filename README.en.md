# ROS Robotics Skill

An open-source engineering-oriented skill / prompt pack for **ROS 1 / ROS 2 robotics development, migration, and integration debugging**.

## What makes it useful

- Detects the workspace before editing code
- Covers `catkin`, `colcon`, TF, URDF/Xacro, Nav2, `ros2_control`, MCU / `micro-ROS`
- Ships runnable helper scripts, not only prose
- Produces minimal, verifiable change plans and regression commands

## Install with Skills CLI

If you already use the Skills CLI, you can install directly from GitHub:

```bash
npx skills add https://github.com/wzyn20051216/ros-robotics-skill -g -y
```

You can also try the short repo form:

```bash
npx skills add wzyn20051216/ros-robotics-skill -g -y
```

> If the short form fails in your environment, prefer the full GitHub URL.

## Quick install

### Linux / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/wzyn20051216/ros-robotics-skill/main/install.sh | bash
```

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/wzyn20051216/ros-robotics-skill/main/install.ps1 | iex
```

## Supported hosts

| Host | Integration |
| --- | --- |
| Codex | Native skill |
| Claude Code | Native skill |
| Gemini CLI | Command pack |

## Project highlights

- Workspace detector: `scripts/detect_ros_workspace.py`
- Consistency checker: `scripts/check_ros_workspace_consistency.py`
- Cross-host installer: `scripts/install.py`
- References for TF, URDF/Xacro, Nav2, `ros2_control`, `micro-ROS`
- CI, tests, community templates, changelog, contributing guide
