# 机器人模型、URDF/Xacro 与 TF

## 适用场景

当任务涉及 `URDF`、`Xacro`、`robot_state_publisher`、RViz、TF 树、传感器外参时加载本参考。

## 推荐检查顺序

1. `robot_description` 是否生成成功
2. `robot_state_publisher` 是否正常启动
3. `joint_states` 是否存在且关节名匹配
4. RViz Fixed Frame 是否正确
5. mesh 路径是否有效且已安装
6. TF 是否单根，静态 / 动态是否分清

## Xacro 建议

- 把底盘、轮组、IMU、LiDAR、相机拆成独立宏
- 把尺寸、外参、mesh 路径参数化
- 把共性结构抽象，不要复制多个近似 URDF 文件

## 常见故障

### RViz 看不到模型

- Fixed Frame 错
- `robot_description` 为空
- mesh 路径错误
- 资源文件未安装
- 没有 `joint_states`

### TF 树断裂

- `base_link`、`odom`、`map` 命名不一致
- 静态变换没启动
- 动态变换时间戳异常
- 同一 TF 被多节点重复发布

## 官方参考

- `robot_state_publisher`：<https://docs.ros.org/en/noetic/api/robot_state_publisher/html/>
- ROS 2 URDF 教程：<https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/Using-URDF-with-Robot-State-Publisher-cpp.html>
- `xacro`：<https://docs.ros.org/en/ros2_packages/jazzy/api/xacro/>
- `tf2` 教程：<https://docs.ros.org/en/galactic/Tutorials/Intermediate/Tf2/Tf2-Main.html>
