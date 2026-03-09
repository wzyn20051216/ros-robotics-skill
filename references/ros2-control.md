# ros2_control 联调参考

## 第一原则

`ros2_control` 问题通常出在 **硬件接口导出、控制器配置、接口类型匹配、读写周期**，而不是先怪控制器本身。

## 检查顺序

1. 硬件组件是 `system`、`sensor` 还是 `actuator`
2. 导出的接口类型是否正确：`position` / `velocity` / `effort`
3. 控制器 YAML 是否与硬件导出的接口一致
4. 控制器是否真正进入 active 状态
5. 硬件读写周期是否稳定

## 常见故障

### 控制器加载失败

- 硬件插件名错
- 参数文件路径错
- 接口类型不匹配
- 依赖包未正确安装

### 控制器启动但机器人不动

- 写接口未真正下发到底层
- 底层驱动忽略了控制量
- 状态反馈频率过低
- 速度 / 位置 / 力矩语义混乱

## 官方与高星参考

- `ros2_control` Getting Started：<https://control.ros.org/master/doc/getting_started/getting_started.html>
- `ros2_controllers`：<https://control.ros.org/humble/doc/ros2_controllers/doc/controllers_index.html>
- `ros2_control` GitHub：<https://github.com/ros-controls/ros2_control>
