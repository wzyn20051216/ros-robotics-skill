# ROS 机器人项目审查清单

## 构建与工作区

- 是否先识别 ROS 1 / ROS 2 / mixed workspace
- 是否沿用现有构建系统，而不是盲目切换 `catkin_make` / `catkin build` / `colcon`
- `package.xml` 与 `CMakeLists.txt` / `setup.py` 是否一致

## 接口与消息

- topic / service / action 命名是否稳定
- 单位、字段语义、命名空间、remap 是否一致
- ROS 2 是否显式处理 QoS

## TF 与时间

- TF 是否单根
- 静态 TF 与动态 TF 是否分对
- 时间戳是否连续
- `frame_id` / `child_frame_id` 是否一致

## 传感器与底盘

- IMU 轴向、LiDAR frame、底盘运动学、编码器方向是否清晰
- 是否有失连保护和超时停车

## 导航与控制

- 定位、里程计、代价地图、控制频率是否与机器人能力匹配
- `/cmd_vel` 链路是否真正闭环

## 嵌入式与总线

- 串口 / CAN 帧格式、校验、时间源是否明确
- 是否存在 ISR 阻塞、动态分配、无界循环、竞态访问
