# SLAM 建图与定位参考

## 第一原则

> SLAM 问题通常出在传感器数据质量、TF 配置和参数调优，而不是算法本身。
> 优先检查里程计精度、激光雷达数据质量和坐标系变换链，再去调算法参数。

## 常用 SLAM 框架对比

| 框架 | 维护方 | 维度 | 特点 |
|------|--------|------|------|
| Cartographer | Google | 2D/3D | 高精度，子图+回环检测，配置复杂 |
| SLAM Toolbox | Steve Macenski | 2D | Nav2 默认推荐，易上手，支持续建 |
| ORB-SLAM3 | 社区 | 3D | 视觉方案，特征点法，对纹理有要求 |
| rtabmap | IntRoLab | 2D/3D | 支持 LiDAR+相机融合，生成 3D 点云地图 |

**选型建议**：室内 2D 首选 SLAM Toolbox；高精度大场景用 Cartographer；视觉用 ORB-SLAM3；多传感器融合用 rtabmap。

## 建图流程

```
传感器校准 → TF 配置 → 启动 SLAM 节点 → 遥控建图 → 保存地图
```

```bash
# 遥控建图典型流程
ros2 launch my_robot bringup.launch.py
ros2 launch slam_toolbox online_async_launch.py
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

## Cartographer 配置要点

```lua
-- my_robot_cartographer.lua
include "map_builder.lua"
include "trajectory_builder.lua"
options = {
  map_builder = MAP_BUILDER,
  trajectory_builder = TRAJECTORY_BUILDER,
  map_frame = "map",
  tracking_frame = "imu_link",        -- 有 IMU 时设为 imu_link
  published_frame = "odom",           -- 发布 map→odom 变换
  odom_frame = "odom",
  provide_odom_frame = false,         -- 使用外部里程计时设 false
  use_odometry = true,
  num_laser_scans = 1,
  num_point_clouds = 0,
  lookup_transform_timeout_sec = 0.2,
}
TRAJECTORY_BUILDER_2D.min_range = 0.12
TRAJECTORY_BUILDER_2D.max_range = 8.0
TRAJECTORY_BUILDER_2D.use_imu_data = true
MAP_BUILDER.use_trajectory_builder_2d = true
return options
```

- `tracking_frame`：有 IMU 必须设为 IMU 所在 frame
- `provide_odom_frame`：有外部里程计时设 `false`

## SLAM Toolbox 配置要点

```yaml
# slam_toolbox_params.yaml
slam_toolbox:
  ros__parameters:
    solver_plugin: solver_plugins::CeresSolver
    ceres_linear_solver: SPARSE_NORMAL_CHOLESKY
    mode: mapping                    # mapping / localization
    resolution: 0.05
    max_laser_range: 12.0
    minimum_travel_distance: 0.5
    odom_frame: odom
    map_frame: map
    base_frame: base_link
    scan_topic: /scan
    do_loop_closing: true
    loop_search_maximum_distance: 3.0
```

模式区别：**online_async**（实时建图）、**online_sync**（同步，每帧必处理）、**offline**（bag 离线建图）。

```bash
ros2 launch slam_toolbox online_async_launch.py params_file:=./slam_toolbox_params.yaml
```

## 地图保存与加载

```bash
# 保存为标准 OccupancyGrid 格式
ros2 run nav2_map_server map_saver_cli -f ~/maps/my_map --ros-args -p save_map_timeout:=10000
```

```yaml
# my_map.yaml - 地图元数据
image: my_map.pgm
mode: trinary
resolution: 0.050000        # 每像素对应的米数
origin: [-5.0, -5.0, 0.0]  # 地图原点 [x, y, yaw]
occupied_thresh: 0.65
free_thresh: 0.25
```

```yaml
# map_server 加载配置
map_server:
  ros__parameters:
    yaml_filename: /home/user/maps/my_map.yaml
    topic_name: map
    frame_id: map
```

## IMU 融合注意事项

IMU 坐标系必须符合 REP-103（x 前、y 左、z 上），安装方向不一致需在静态 TF 中旋转。使用 `robot_localization`（EKF）融合 IMU 和轮式里程计：

```yaml
# ekf.yaml
ekf_filter_node:
  ros__parameters:
    frequency: 30.0
    two_d_mode: true
    odom_frame: odom
    base_link_frame: base_link
    world_frame: odom
    odom0: /wheel_odom
    odom0_config: [true, true, false,
                   false, false, true,
                   false, false, false,
                   false, false, true,
                   false, false, false]
    imu0: /imu/data
    imu0_config: [false, false, false,
                  false, false, true,
                  false, false, false,
                  false, false, true,
                  false, false, false]
    imu0_remove_gravitational_acceleration: true
```

## 回环检测

当机器人回到之前到过的位置时，SLAM 通过特征匹配识别同一地点来修正累积漂移。成功时大幅消除漂移；失败则出现重影或错位。

常见失败原因：环境特征不足（长走廊）、环境高度重复（仓库货架）、运动过快导致累积误差超出搜索范围。

## 常见故障

| 现象 | 可能原因 | 排查方法 |
|------|---------|---------|
| 建图飘移严重 | 里程计差/IMU未融合/TF错 | `ros2 topic echo /odom` 确认数据合理 |
| 地图有重影 | 回环失败/编码器打滑 | 降低建图速度，增加回环搜索距离 |
| 地图无法保存 | topic 名错/服务未启动 | `ros2 topic list` 确认 `/map` 存在 |
| SLAM 启动即崩溃 | TF 树不完整 | `ros2 run tf2_tools view_frames` |

## 官方与高星参考

- [Cartographer ROS 文档](https://google-cartographer-ros.readthedocs.io/)
- [SLAM Toolbox GitHub](https://github.com/SteveMacenski/slam_toolbox)
- [Nav2 SLAM 教程](https://docs.nav2.org/tutorials/docs/navigation2_with_slam.html)
- [robot_localization Wiki](https://docs.ros.org/en/humble/p/robot_localization/)
