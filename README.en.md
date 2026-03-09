# ROS Robotics Skill

An open-source engineering-oriented skill / prompt pack for **ROS 1 / ROS 2 robotics development, migration, and integration debugging**.

## What makes it useful

- Detects the workspace before editing code
- Covers `catkin`, `colcon`, TF, URDF/Xacro, Nav2, `ros2_control`, MCU / `micro-ROS`
- Ships runnable helper scripts, not only prose
- Produces minimal, verifiable change plans and regression commands

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
