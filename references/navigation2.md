# Navigation2 联调参考

## 第一原则

Nav2 问题很少只是“规划器参数不对”，通常是 **TF、定位、里程计、控制链路、底盘反馈** 的系统问题。

## 联调顺序

1. TF 是否完整
2. 地图与定位是否可信
3. 里程计是否稳定
4. `/cmd_vel` 是否真正到达底盘
5. 底盘是否按正确单位解释速度
6. 控制频率与机器人能力是否匹配

## 常见故障

### Nav2 已激活但机器人不动

- `/cmd_vel` 未生成
- QoS 不兼容
- 底盘未真正订阅到控制命令
- 安全锁 / 急停 / 超时保护生效
- TF 不完整导致闭环未形成

### 会动但方向不对

- 坐标系定义错
- 速度单位错
- 左右轮方向或轮距参数错
- IMU 朝向或里程计积分方向错

## 官方与高星参考

- Nav2 Getting Started：<https://docs.nav2.org/getting_started/>
- Nav2 GitHub：<https://github.com/ros-navigation/navigation2>
