# MoveIt 2 运动规划参考

## 第一原则

MoveIt 2 问题通常出在 URDF/SRDF 配置、运动学插件、碰撞矩阵和规划器参数，而不是运动规划算法本身。常见根因排序：SRDF 规划组定义错误 > 运动学插件参数不当 > 碰撞矩阵过严 > 控制器接口不匹配。

## 核心架构

- **move_group 节点**：中心协调节点，接收规划请求并调度各子系统
- **Planning Scene**：维护世界模型（机器人状态 + 环境障碍物），用于碰撞检测
- **Motion Planning Pipeline**：规划器适配层，支持 OMPL、Pilz 等后端
- **Controller Interface**：通过 FollowJointTrajectory action 与 ros2_control 对接

协作链路：`用户请求 → MoveIt 规划 → FollowJointTrajectory → ros2_control 控制器 → 硬件执行`

## 配置包生成

```bash
sudo apt install ros-humble-moveit-setup-assistant
ros2 launch moveit_setup_assistant setup_assistant.launch.py
```

生成结构：`config/`（kinematics.yaml、ompl_planning.yaml、moveit_controllers.yaml、joint_limits.yaml）、`launch/`（move_group.launch.py、demo.launch.py）、`srdf/my_robot.srdf`。

## SRDF 关键配置

```xml
<robot name="my_robot">
  <group name="manipulator">
    <chain base_link="base_link" tip_link="tool0"/>
  </group>
  <end_effector name="gripper" parent_link="tool0"
                group="gripper_group" parent_group="manipulator"/>
  <group_state name="home" group="manipulator">
    <joint name="joint_1" value="0.0"/>
    <joint name="joint_2" value="-1.57"/>
    <joint name="joint_3" value="1.57"/>
  </group_state>
  <!-- 碰撞矩阵（ACM）：禁用不需要检测碰撞的链接对 -->
  <disable_collisions link1="base_link" link2="link_1" reason="Adjacent"/>
  <disable_collisions link1="base_link" link2="link_3" reason="Never"/>
</robot>
```

ACM 过严导致规划失败，过松导致碰撞遗漏。Setup Assistant 自动采样生成，复杂机器人需手动审查。

## 运动学插件

| 插件 | 特点 | 适用场景 |
|------|------|----------|
| KDL | 默认通用，数值迭代，较慢 | 快速验证、原型开发 |
| IKFast | 解析解，极快但需预生成 | 6DOF 标准构型，生产环境 |
| TRAC-IK | 数值+SQP 双求解，鲁棒 | **推荐默认选择** |

```yaml
# kinematics.yaml — 推荐 TRAC-IK
manipulator:
  kinematics_solver: trac_ik_kinematics_plugin/TRAC_IKKinematicsPlugin
  kinematics_solver_search_resolution: 0.005
  kinematics_solver_timeout: 0.05
  solve_type: Distance  # Speed | Distance | Manipulation1
```

## 规划器配置

```yaml
# ompl_planning.yaml — OMPL 默认采样规划器
manipulator:
  default_planner_config: RRTConnect
  planner_configs:
    RRTConnect:
      type: geometric::RRTConnect
      range: 0.0  # 0 表示自动计算步长
  longest_valid_segment_fraction: 0.005
```

```yaml
# Pilz 工业运动规划器 — 确定性运动（PTP/LIN/CIRC）
planning_plugin: pilz_industrial_motion_planner/CommandPlanner
```

调参建议：`planning_time` 默认 5 秒，复杂场景增至 10-30 秒；`num_planning_attempts` 设 5-10 次。

## MoveIt 2 C++ API 示例

```cpp
#include <moveit/move_group_interface/move_group_interface.h>

auto move_group = moveit::planning_interface::MoveGroupInterface(node, "manipulator");

// 设置目标位姿并规划执行
geometry_msgs::msg::Pose target_pose;
target_pose.position.x = 0.4;
target_pose.position.z = 0.5;
target_pose.orientation.w = 1.0;
move_group.setPoseTarget(target_pose);

moveit::planning_interface::MoveGroupInterface::Plan plan;
if (move_group.plan(plan) == moveit::core::MoveItErrorCode::SUCCESS) {
  move_group.execute(plan);
}

// 笛卡尔路径规划（直线运动）
std::vector<geometry_msgs::msg::Pose> waypoints = {target_pose};
target_pose.position.z -= 0.1;
waypoints.push_back(target_pose);
moveit_msgs::msg::RobotTrajectory trajectory;
double fraction = move_group.computeCartesianPath(waypoints, 0.01, 0.0, trajectory);
if (fraction > 0.95) move_group.execute(trajectory);
```

## Launch 集成

```python
from launch import LaunchDescription
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():
    moveit_config = MoveItConfigsBuilder(
        "my_robot", package_name="my_robot_moveit_config"
    ).to_moveit_configs()
    return LaunchDescription([
        Node(package="moveit_ros_move_group", executable="move_group",
             output="screen",
             parameters=[moveit_config.to_dict(), {"use_sim_time": True}]),
    ])
```

## 常见故障

### 规划失败

| 现象 | 原因 | 解决方案 |
|------|------|----------|
| 始终无解 | ACM 过严 | 重新生成碰撞矩阵，检查 "Never" 标记 |
| IK 无解 | 目标在工作空间外或奇异点 | 检查位姿合理性，换用 TRAC-IK |
| 规划超时 | 窄通道或高维空间 | 增大 `planning_time`，换用 PRM |
| 起始状态无效 | 关节角度未正确发布 | 检查 `/joint_states` 话题 |

### 执行失败

| 现象 | 原因 | 解决方案 |
|------|------|----------|
| 控制器未连接 | action server 未启动 | 确认 ros2_control 控制器已激活 |
| 轨迹超限 | 超出 `joint_limits.yaml` | 检查限位与 URDF 一致性 |
| 跟踪误差过大 | PID 不匹配或频率低 | 调整 PID，频率提至 500Hz+ |

### RViz 与仿真问题

- **Interactive Marker 不出现**：确认 MotionPlanning 插件已加载，`planning_group` 与 SRDF 一致
- **仿真轨迹抖动**：控制频率需 ≥ 200Hz、PID 未针对仿真调优、URDF 惯性参数不合理

## 与 Gazebo 联合仿真

架构：`MoveIt → FollowJointTrajectory → ros2_control → GazeboSystem → Gazebo 物理引擎`

```yaml
# ros2_control 硬件接口切换（MoveIt 配置层无需更改）
# fake:   mock_components/GenericSystem
# gazebo: gazebo_ros2_control/GazeboSystem
# 真实:   对应硬件驱动插件
```

## 官方与高星参考

- [MoveIt 2 官方文档](https://moveit.picknik.ai/main/index.html) — 权威配置与 API 参考
- [moveit2_tutorials](https://github.com/moveit/moveit2_tutorials) — 官方教程与完整示例
- [MoveIt 2 GitHub](https://github.com/moveit/moveit2) — 源码与 issue 讨论
- [ros2_control 文档](https://control.ros.org) — 控制器集成参考
