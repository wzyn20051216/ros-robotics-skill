# Foxglove / PlotJuggler 数据可视化参考

## 第一原则

数据可视化是 ROS 调试的利器，Foxglove 擅长多模态数据和 mcap 回放，PlotJuggler 擅长时序数据分析。先明确需求再选工具。

- 实时调试机器人状态 → 优先考虑 Foxglove Studio 或 PlotJuggler
- 离线回放录制数据 → mcap + Foxglove 是最佳组合
- 纯时序数值分析（PID 调参、传感器信号） → PlotJuggler 更直观
- 空间数据（点云、TF、URDF） → Foxglove 3D 面板或 RViz

## 工具对比

| 维度 | Foxglove Studio | PlotJuggler | RViz |
|------|----------------|-------------|------|
| 连接方式 | foxglove_bridge WebSocket / mcap 文件拖入 | ROS 2 Topic Subscriber / rosbag 文件 | 直接订阅 ROS 2 话题 |
| 擅长场景 | 多模态数据、离线回放、远程调试、团队协作 | 时序数值绘图、多信号对比、PID 调参 | 3D 空间可视化、TF 树、传感器融合 |
| 安装方式 | 下载桌面客户端（跨平台）或 Web 版 | `apt install` 或 snap | ROS 内置，`apt install` |
| 数据格式支持 | mcap、ros2 bag、自定义插件 | ros2 bag、CSV、实时 topic | 仅实时 ROS 话题 |

## Foxglove Studio

### 连接 ROS 2

安装 foxglove_bridge（机器人端）：

```bash
sudo apt install ros-$ROS_DISTRO-foxglove-bridge
```

启动 bridge 服务：

```bash
ros2 launch foxglove_bridge foxglove_bridge_launch.xml
```

自定义端口和主机（可选）：

```bash
ros2 launch foxglove_bridge foxglove_bridge_launch.xml \
  port:=8765 \
  address:=0.0.0.0
```

在 Foxglove Studio 客户端中：
- 点击左上角 "Open connection"
- 选择 "Foxglove WebSocket" → 填写 `ws://机器人IP:8765`
- 或选择 "Rosbridge WebSocket" → 填写 `ws://机器人IP:9090`

### 常用面板

**3D 面板**
- 显示 URDF 机器人模型：添加 URDF 数据源，指定 `/robot_description`
- 点云可视化：添加 `/scan` 或 `/cloud_registered` 话题
- TF 树实时渲染：勾选 Show TF frames

**Plot 面板**
- 时序数据绘图，支持 message path 表达式
- 示例表达式：`/odom.pose.pose.position.x`、`/cmd_vel.linear.x`
- 支持多曲线叠加对比，可设置 Y 轴范围

**Raw Messages 面板**
- 查看原始消息 JSON 结构，适合调试自定义消息类型
- 支持消息字段展开/折叠

**Log 面板**
- 过滤 `/rosout` 日志，支持按级别（DEBUG/INFO/WARN/ERROR）筛选
- 支持关键字搜索

**Image 面板**
- 显示 `/camera/image_raw` 等相机话题
- 支持压缩图像 `sensor_msgs/CompressedImage`

**Diagnostics 面板**
- 可视化 `/diagnostics` 话题中各硬件模块状态
- 颜色编码：绿色正常、黄色警告、红色错误

### 布局管理

保存当前布局：
- 菜单 → Layout → "Save layout" → 导出为 `.json` 文件

推荐布局模板：

**导航调试布局**（三栏）：
- 左：3D 面板（地图 + 机器人 + 点云）
- 中：Plot 面板（速度、里程计）
- 右：Log 面板 + Diagnostics

**控制调试布局**（两栏）：
- 左：Plot 面板（设定值 vs 实际值）
- 右：Raw Messages（控制器状态话题）

导入布局 JSON：菜单 → Layout → "Import from file"

### 与 mcap 结合

录制为 mcap 格式：

```bash
# 录制指定话题为 mcap 格式
ros2 bag record -s mcap -o my_bag /odom /scan /tf /cmd_vel

# 录制所有话题
ros2 bag record -s mcap -o full_bag --all
```

回放控制：
- 将 `.mcap` 文件直接拖入 Foxglove Studio 窗口
- 使用底部时间轴拖动到任意时刻
- 支持 0.25x / 1x / 2x / 5x 倍速播放
- 所有面板自动同步到当前播放时刻

查看 mcap 文件元信息：

```bash
# 安装 mcap CLI 工具
pip install mcap

# 查看 bag 中话题列表和消息统计
mcap info my_bag.mcap
```

### 消息过滤和转换

message path 表达式示例：

```
# 提取里程计位置 X
/odom.pose.pose.position.x

# 提取 IMU 角速度 Z
/imu/data.angular_velocity.z

# 提取数组中第一个元素
/joint_states.position[0]

# 多层嵌套
/move_base/feedback.feedback.base_position.pose.position.x
```

自定义扩展面板（JavaScript）：
- 菜单 → Extensions → "Create extension"
- 可订阅任意话题，自定义渲染逻辑

## PlotJuggler

### 安装

通过 apt 安装（推荐）：

```bash
sudo apt install ros-$ROS_DISTRO-plotjuggler-ros
```

通过 snap 安装：

```bash
sudo snap install plotjuggler
```

### 连接 ROS 2

启动 PlotJuggler：

```bash
ros2 run plotjuggler plotjuggler
```

连接实时数据：
1. 点击工具栏 "Streaming" → 选择 "ROS2 Topic Subscriber"
2. 点击 "Start" 开始订阅
3. 左侧话题列表中，将字段名直接拖拽到右侧绘图区

### 常用操作

**多 topic 对比绘图**
- 同时拖入 `/cmd_vel.linear.x` 和 `/odom.twist.twist.linear.x`
- 两条曲线叠加在同一坐标系，直观对比设定值与实际值

**时间对齐和偏移**
- 右键曲线 → "Time offset" → 输入偏移量（秒）
- 用于补偿传感器延迟或时钟不同步

**导出 CSV**
- 选中曲线 → 右键 → "Export to CSV"
- 适合后续用 Python / MATLAB 进一步分析

**加载 rosbag 文件**

```bash
# 确保已安装 ros2 bag 插件
sudo apt install ros-$ROS_DISTRO-plotjuggler-ros
```

- File → "Load Data File" → 选择 `.db3` 或 `.mcap` 文件
- 所有话题字段自动解析到左侧列表

**Lua 脚本数据变换**
- Tools → "Custom Series" → 编写 Lua 脚本
- 示例：计算速度误差

```lua
-- 返回两个信号的差值
return value1 - value2
```

## 调试工作流

### 典型调试场景

**1. 控制器调优（PID 参数整定）**

```bash
# 启动 PlotJuggler 并订阅控制相关话题
ros2 run plotjuggler plotjuggler &
# 同时发布测试指令
ros2 topic pub /cmd_vel geometry_msgs/Twist '{linear: {x: 0.5}}'
```

- PlotJuggler 同时绘制 `/cmd_vel.linear.x`（设定值）和 `/odom.twist.twist.linear.x`（实际值）
- 观察响应曲线，调整 P/I/D 参数，直到超调量和稳态误差满足要求

**2. SLAM 质量评估**

- Foxglove 3D 面板同时显示：`/map`、`/scan`、`/tf`（odom → base_link）
- Plot 面板绘制定位协方差：`/amcl_pose.pose.covariance[0]`
- 协方差持续上升说明定位发散，需重新建图或调整参数

**3. 传感器延迟分析**

```bash
# 录制两个传感器话题
ros2 bag record -s mcap -o delay_test /imu/data /odom
```

- Foxglove Plot 面板分别绘制两者时间戳字段
- 计算时间差：`/imu/data.header.stamp` vs `/odom.header.stamp`

**4. 离线分析完整流程**

```bash
# 1. 录制数据
ros2 bag record -s mcap -o test_run --all

# 2. 拖入 Foxglove 回放，截图记录关键帧
# 3. 用 PlotJuggler 加载同一 bag 做数值分析
# 4. 导出 CSV 后用 Python 绘制最终图表
python3 analyze.py test_data.csv
```

## 常见问题

| 问题现象 | 排查步骤 |
|---------|---------|
| Foxglove 连接失败 | 检查 foxglove_bridge 是否启动；确认端口 8765 未被占用；检查防火墙是否放行该端口 |
| 面板无数据显示 | 确认话题名称拼写正确；检查消息类型是否匹配；验证 QoS 设置（如 BEST_EFFORT vs RELIABLE） |
| PlotJuggler 无法加载 ros2 bag | 确认已安装 `ros-$ROS_DISTRO-plotjuggler-ros` 插件；确认 bag 格式为 `.db3` 或 `.mcap` |
| mcap 播放卡顿 | 文件过大时先裁剪：`ros2 bag filter`；确认磁盘为 SSD；关闭不需要的面板减少渲染开销 |
| TF 树显示异常 | 运行 `ros2 run tf2_tools view_frames` 检查 TF 链是否完整 |

## 官方与高星参考

- **Foxglove 官网与文档**：https://foxglove.dev/docs
- **foxglove_bridge GitHub**：https://github.com/foxglove/ros-foxglove-bridge
- **PlotJuggler GitHub**：https://github.com/facontidavide/PlotJuggler（Star 4k+）
- **mcap 官方文档**：https://mcap.dev/docs
- **mcap CLI 工具**：https://github.com/foxglove/mcap
