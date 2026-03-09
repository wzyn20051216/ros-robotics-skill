# Contributing

感谢你愿意改进 `ros-robotics`。

## 贡献方向

欢迎提交以下类型的贡献：

- 新的 ROS 专题参考文档
- 更准确的工作区检测 / 一致性检查逻辑
- 新的真实案例
- 对 Codex / Claude Code / Gemini CLI 的更好安装体验
- 文档修正、兼容矩阵补充、CI 改进

## 提交前请先做这些事

```bash
python -m unittest discover -s tests -p "test_*.py"
python scripts/detect_ros_workspace.py .
python scripts/check_ros_workspace_consistency.py .
```

## 文档约定

- 说明“何时用、何时不用”
- 尽量给最小复现实例
- 对关键判断给出处或工程依据
- 不要堆砌空泛概念

## PR 检查单

- [ ] 我已经描述清楚这个改动解决什么问题
- [ ] 我已经说明适用范围与边界
- [ ] 我已经运行最小测试或说明无法运行的原因
- [ ] 我没有引入与主题无关的大改动
