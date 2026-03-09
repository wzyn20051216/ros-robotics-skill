# Changelog

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
