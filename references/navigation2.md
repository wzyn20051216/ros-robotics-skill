# Navigation2 联调参考

## 第一原则

Nav2 问题很少只是"规划器参数不对"，通常是 **TF、定位、里程计、控制链路、底盘反馈** 的系统问题。

## 联调顺序

1. TF 是否完整
2. 地图与定位是否可信
3. 里程计是否稳定
4. `/cmd_vel` 是否真正到达底盘
5. 底盘是否按正确单位解释速度
6. 控制频率与机器人能力是否匹配

## Nav2 参数调优模板

以下是 `nav2_params.yaml` 中最关键的参数片段，实际使用时根据机器人尺寸和硬件能力调整：

```yaml
controller_server:
  ros__parameters:
    controller_frequency: 20.0          # 控制频率，底盘响应慢可降到 10
    min_x_velocity_threshold: 0.001
    min_y_velocity_threshold: 0.5
    min_theta_velocity_threshold: 0.001
    progress_checker_plugins: ["progress_checker"]
    goal_checker_plugins: ["goal_checker"]
    controller_plugins: ["FollowPath"]
    progress_checker:
      plugin: "nav2_controller::SimpleProgressChecker"
      required_movement_radius: 0.5
      movement_time_allowance: 10.0
    goal_checker:
      plugin: "nav2_controller::SimpleGoalChecker"
      xy_goal_tolerance: 0.25           # 到达目标点的位置容差
      yaw_goal_tolerance: 0.25          # 到达目标点的角度容差
      stateful: true
    FollowPath:
      plugin: "dwb_core::DWBLocalPlanner"
      max_vel_x: 0.5                    # 最大前进速度 m/s
      min_vel_x: 0.0
      max_vel_y: 0.0                    # 差速底盘设为 0
      max_vel_theta: 1.0                # 最大旋转速度 rad/s
      min_speed_xy: 0.0
      max_speed_xy: 0.5
      acc_lim_x: 2.5                    # 前进加速度限制
      acc_lim_theta: 3.2                # 旋转加速度限制
      decel_lim_x: -2.5
      decel_lim_theta: -3.2

planner_server:
  ros__parameters:
    planner_plugins: ["GridBased"]
    GridBased:
      plugin: "nav2_navfn_planner::NavfnPlanner"
      tolerance: 0.5                    # 目标容差，值过小可能导致找不到路径
      use_astar: false                  # true 使用 A*，false 使用 Dijkstra
      allow_unknown: true               # 允许在未知区域规划

bt_navigator:
  ros__parameters:
    global_frame: map
    robot_base_frame: base_link
    odom_topic: /odom
    default_nav_to_pose_bt_xml: ""      # 空表示使用默认行为树
    plugin_lib_names:
      - nav2_compute_path_to_pose_action_bt_node
      - nav2_follow_path_action_bt_node
      - nav2_clear_costmap_service_bt_node
      - nav2_is_stuck_condition_bt_node
      - nav2_goal_reached_condition_bt_node
      - nav2_rate_controller_bt_node
      - nav2_recovery_node_bt_node
```

## Costmap 配置示例

```yaml
global_costmap:
  global_costmap:
    ros__parameters:
      update_frequency: 1.0             # 全局地图更新频率，不需要太高
      publish_frequency: 1.0
      global_frame: map
      robot_base_frame: base_link
      robot_radius: 0.22                # 机器人半径，务必测量准确
      resolution: 0.05                  # 地图分辨率 m/pixel
      track_unknown_space: true
      plugins: ["static_layer", "obstacle_layer", "inflation_layer"]
      static_layer:
        plugin: "nav2_costmap_2d::StaticLayer"
        map_subscribe_transient_local: true
      obstacle_layer:
        plugin: "nav2_costmap_2d::ObstacleLayer"
        enabled: true
        observation_sources: scan
        scan:
          topic: /scan
          max_obstacle_height: 2.0
          clearing: true
          marking: true
          data_type: "LaserScan"
          raytrace_max_range: 3.0
          raytrace_min_range: 0.0
          obstacle_max_range: 2.5
          obstacle_min_range: 0.0
      inflation_layer:
        plugin: "nav2_costmap_2d::InflationLayer"
        cost_scaling_factor: 3.0        # 衰减速度，越大衰减越快
        inflation_radius: 0.55          # 膨胀半径，应 > robot_radius

local_costmap:
  local_costmap:
    ros__parameters:
      update_frequency: 5.0             # 局部地图需要更高的更新频率
      publish_frequency: 2.0
      global_frame: odom
      robot_base_frame: base_link
      rolling_window: true
      width: 3                          # 局部地图宽度 m
      height: 3                         # 局部地图高度 m
      resolution: 0.05
      robot_radius: 0.22
      plugins: ["voxel_layer", "inflation_layer"]
      voxel_layer:
        plugin: "nav2_costmap_2d::VoxelLayer"
        enabled: true
        observation_sources: scan
        scan:
          topic: /scan
          max_obstacle_height: 2.0
          clearing: true
          marking: true
          data_type: "LaserScan"
      inflation_layer:
        plugin: "nav2_costmap_2d::InflationLayer"
        cost_scaling_factor: 3.0
        inflation_radius: 0.55
```

## 定位验证（AMCL）

### AMCL 关键参数

- `min_particles` / `max_particles`：粒子数量，环境越大需要越多，建议 500~5000
- `laser_model_type`：激光模型类型，通常用 `likelihood_field`
- `transform_tolerance`：TF 容差，网络延迟大时适当增大（默认 1.0s）
- `initial_pose`：初始位姿，如果机器人每次起点固定可以设定

### 定位验证步骤

```bash
# 1. 确认 AMCL 节点运行且产生粒子云
ros2 topic echo /particlecloud --once

# 2. 确认 map->odom TF 由 AMCL 发布
ros2 run tf2_ros tf2_echo map odom

# 3. 检查 AMCL 更新频率
ros2 topic hz /amcl_pose

# 4. 在 RViz 中观察粒子收敛情况
# 粒子应在机器人移动后快速收敛到一个簇

# 5. 手动设初始位姿后验证
ros2 topic pub /initialpose geometry_msgs/msg/PoseWithCovarianceStamped \
  "{header: {frame_id: 'map'}, pose: {pose: {position: {x: 0.0, y: 0.0}, orientation: {w: 1.0}}}}" --once
```

## /cmd_vel 链路调试

当 Nav2 看起来正常但机器人不动时，按如下顺序排查：

```bash
# 1. 确认 Nav2 是否在发布速度命令
ros2 topic echo /cmd_vel

# 2. 检查发布频率（应接近 controller_frequency）
ros2 topic hz /cmd_vel

# 3. 确认 topic 名称和 QoS 是否匹配
ros2 topic info /cmd_vel -v

# 4. 检查是否有 mux 或中间节点转发（如 twist_mux）
ros2 node list | grep -i mux

# 5. 检查底盘驱动节点是否真的订阅了 /cmd_vel
ros2 node info <底盘节点名> | grep -A5 Subscriptions

# 6. 发送测试速度（绕过 Nav2，直接验证底盘）
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.1}, angular: {z: 0.0}}" -r 10
```

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

### Costmap 膨胀过大导致无法通过窄通道

- `inflation_radius` 设置过大，超出实际机器人尺寸太多
- `cost_scaling_factor` 过小，代价衰减太慢
- 排查：在 RViz 中可视化 costmap，观察膨胀范围是否合理
- 修复：将 `inflation_radius` 设为 `robot_radius + 0.05~0.1m`，增大 `cost_scaling_factor`

### Costmap 膨胀过小导致频繁碰撞

- `robot_radius` 设置比实际机器人小
- `inflation_radius` 小于 `robot_radius`
- 排查：机器人边缘是否在 costmap 代价区域外
- 修复：精确测量机器人最大外廓半径，`inflation_radius` 至少为 `robot_radius * 1.2`

### 规划器找不到路径

- 起点或终点在障碍物内部（costmap 膨胀覆盖了目标点）
- `tolerance` 参数过小
- 地图与实际环境严重不一致
- `allow_unknown` 为 false 但目标在未探索区域
- 排查：`ros2 service call /planner_server/...` 手动触发规划并观察返回值

### 控制器震荡（机器人抖动/左右摇摆）

- 控制频率与底盘响应不匹配
- 速度限制（`max_vel_x`, `max_vel_theta`）超出底盘实际能力
- 加速度限制过大导致超调
- 排查：录制 `/cmd_vel` 数据并绘图，观察速度曲线是否平滑
- 修复：降低最大速度、降低加速度限制、适当增大 `goal_checker` 容差

## 官方与高星参考

- Nav2 Getting Started：<https://docs.nav2.org/getting_started/>
- Nav2 GitHub：<https://github.com/ros-navigation/navigation2>
- Nav2 配置指南：<https://docs.nav2.org/configuration/>
- Nav2 调优指南：<https://docs.nav2.org/tuning/>
- Nav2 Costmap2D 文档：<https://docs.nav2.org/configuration/packages/configuring-costmaps.html>
- AMCL 配置参考：<https://docs.nav2.org/configuration/packages/configuring-amcl.html>
- Nav2 行为树说明：<https://docs.nav2.org/behavior_trees/>
- DWB Controller 参数：<https://docs.nav2.org/configuration/packages/dwb-params/>
