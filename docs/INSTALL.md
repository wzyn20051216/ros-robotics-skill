# 安装说明

## 依赖

- `git`
- `python 3.9+`

## 一键安装

### Linux / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/wzyn20051216/ros-robotics-skill/main/install.sh | bash
```

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/wzyn20051216/ros-robotics-skill/main/install.ps1 | iex
```

## 指定目标主机

### Bash

```bash
curl -fsSL https://raw.githubusercontent.com/wzyn20051216/ros-robotics-skill/main/install.sh | bash -s -- --target codex
curl -fsSL https://raw.githubusercontent.com/wzyn20051216/ros-robotics-skill/main/install.sh | bash -s -- --target claude
curl -fsSL https://raw.githubusercontent.com/wzyn20051216/ros-robotics-skill/main/install.sh | bash -s -- --target gemini
```

### PowerShell

```powershell
$env:ROS_ROBOTICS_TARGET='codex'; irm https://raw.githubusercontent.com/wzyn20051216/ros-robotics-skill/main/install.ps1 | iex
$env:ROS_ROBOTICS_TARGET='claude'; irm https://raw.githubusercontent.com/wzyn20051216/ros-robotics-skill/main/install.ps1 | iex
$env:ROS_ROBOTICS_TARGET='gemini'; irm https://raw.githubusercontent.com/wzyn20051216/ros-robotics-skill/main/install.ps1 | iex
```

## 本地源码安装

```bash
git clone https://github.com/wzyn20051216/ros-robotics-skill.git
cd ros-robotics-skill
python scripts/install.py --target codex --force
python scripts/install.py --target claude --force
python scripts/install.py --target gemini --force
```
