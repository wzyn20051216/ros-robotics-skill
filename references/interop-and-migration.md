# ROS 1 / ROS 2 互通与迁移

## 第一原则

- 先分层，再迁移
- 先桥接，再重构
- 先统一消息、参数、TF 和 topic 语义，再迁实现

## 推荐路径

1. 稳定接口定义
2. 把纯算法和协议层从 ROS API 封装中拆出来
3. 先迁边缘节点，再迁核心控制 / 导航链路
4. 通过 `ros1_bridge` 或网关维持联通

## 注意事项

- 不要在一个包里混写 `catkin` 与 `ament`
- `ros1_bridge` 受 Ubuntu 和 ROS 发行版组合限制
- Ubuntu 24.04 不支持 ROS 1 / `ros1_bridge`

## 官方参考

- REP-149：<https://www.ros.org/reps/rep-0149.html>
- `ros1_bridge`：<https://docs.ros.org/en/humble/p/ros1_bridge/>
