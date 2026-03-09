# ROS 现场排障 Playbooks

## 总原则

不要一上来改代码，先走证据链。

## Playbook 1：能编译但节点起不来

1. 是否 source 了正确环境
2. launch / launch.py 路径是否正确
3. 资源文件是否被正确安装
4. Python 节点入口、权限、依赖是否正确
5. 参数 YAML 是否能被加载

### 具体排查命令

```bash
# 检查环境是否正确
echo $ROS_DISTRO
echo $AMENT_PREFIX_PATH

# 确认包已安装
ros2 pkg list | grep <包名>

# 查看包的可执行文件
ros2 pkg executables <包名>

# 单独启动节点（绕过 launch，定位是节点问题还是 launch 问题）
ros2 run <包名> <节点名> --ros-args --log-level debug

# 检查 Python 入口点（setup.py / setup.cfg 中 console_scripts）
cat install/<包名>/lib/<包名>/<节点名>

# 查看是否有权限问题
ls -la install/<包名>/lib/<包名>/
```

## Playbook 2：topic 存在，但系统表现不对

1. topic 名称是否对
2. 发布频率是否合理
3. 时间戳是否连续
4. `frame_id` 是否正确
5. 单位是否统一
6. QoS 是否匹配（ROS 2）

### 具体排查命令

```bash
# 列出所有 topic
ros2 topic list

# 查看 topic 详细信息（类型、发布者/订阅者数量、QoS）
ros2 topic info /scan -v

# 检查发布频率
ros2 topic hz /scan

# 查看消息内容（检查 frame_id、时间戳、数据值）
ros2 topic echo /scan --once

# 检查消息延迟
ros2 topic delay /scan

# 检查带宽占用
ros2 topic bw /scan

# 如果怀疑 QoS 不匹配
ros2 doctor --report | grep -A5 "QoS"
```

## Playbook 3：MCU 联调时偶发异常

1. 总线吞吐是否足够
2. 时间戳来自哪里
3. 丢包与重传是否可观测
4. 主机侧是否单线程做了耗时解析
5. 板端是否存在阻塞、动态分配、无界重试

### 具体排查命令

```bash
# 检查串口连接状态
ls -la /dev/ttyUSB* /dev/ttyACM*
stty -F /dev/ttyUSB0

# 抓取原始串口数据（验证通信是否正常）
cat /dev/ttyUSB0 | xxd | head -50

# 监控串口通信（需安装 minicom 或 picocom）
minicom -D /dev/ttyUSB0 -b 115200

# 检查 USB 设备信息
lsusb
dmesg | tail -20

# 监控 CPU 占用（定位是否有阻塞）
top -p $(pgrep -f <节点名>)
```

## Playbook 4：TF 树断裂导致功能异常

TF 问题是 ROS 系统中最常见的隐性故障来源。表现为导航失败、RViz 显示异常、传感器数据无法正确融合。

### 症状

- RViz 中出现 "No transform from [xxx] to [yyy]" 警告
- Nav2 无法激活或激活后不工作
- 传感器数据在 RViz 中位置偏移或不显示
- `lookupTransform` 抛出异常

### 排查步骤

```bash
# 1. 生成 TF 树的 PDF 可视化图（最直观的方法）
ros2 run tf2_tools view_frames
# 生成 frames.pdf，检查：
# - 是否有断开的分支
# - 每个变换的发布者和频率
# - 是否有过期的变换

# 2. 实时查看两个坐标系之间的变换
ros2 run tf2_ros tf2_echo map base_link
# 确认变换存在且数值合理

# 3. 监听所有 TF 广播
ros2 topic echo /tf
ros2 topic echo /tf_static

# 4. 检查 TF 发布频率
ros2 topic hz /tf

# 5. 使用 tf2_monitor 查看所有变换的延迟和频率
ros2 run tf2_ros tf2_monitor

# 6. 检查是否有重复的 TF 发布者（常见问题）
ros2 topic info /tf -v
# 如果多个节点发布同一个变换，会导致跳变

# 7. 常见的完整 TF 链路（差速机器人 + Nav2）
# map -> odom -> base_link -> [sensor_frames]
#   ^       ^
#   |       |
#  AMCL  odom_publisher / diff_drive_controller
```

### 常见修复

- 缺少 `robot_state_publisher`：确保 launch 中包含且加载了正确的 URDF
- 缺少 `static_transform_publisher`：传感器外参需要手动发布
- TF 时间戳过期：检查发布频率和 `transform_tolerance` 参数

## Playbook 5：参数加载失败或不生效

### 症状

- 节点使用默认参数而非配置文件中的值
- 启动时报 `Parameter not declared` 错误
- 修改 YAML 后重启节点参数没有变化

### 排查步骤

```bash
# 1. 列出节点的所有参数
ros2 param list /节点名

# 2. 获取特定参数的当前值
ros2 param get /节点名 参数名

# 3. 查看参数的描述和类型约束
ros2 param describe /节点名 参数名

# 4. 运行时动态修改参数（测试用）
ros2 param set /节点名 参数名 新值

# 5. 导出节点当前所有参数（与 YAML 文件对比）
ros2 param dump /节点名

# 6. 检查 launch 文件中参数加载是否正确
# 常见错误：
#   - parameters 用了列表但忘了文件路径前的逗号
#   - YAML 缩进错误导致参数挂到了错误的命名空间
#   - 节点名/命名空间与 YAML 中的不匹配
```

### YAML 格式常见陷阱

```yaml
# 错误：缩进不一致（混用 tab 和空格）
node_name:
  ros__parameters:
    param1: 1.0
	param2: 2.0          # 这里用了 tab，会导致解析失败

# 错误：命名空间层级错误
controller_server:
  ros__parameters:
    FollowPath:
      plugin: "dwb_core::DWBLocalPlanner"
    max_vel_x: 0.5       # 这个参数不在 FollowPath 下面！

# 错误：字符串 vs 数字
param_a: 1.0             # float
param_b: "1.0"           # string — 如果节点期望 float 会报错

# 错误：布尔值写法
use_sim_time: True        # 应该是 true（小写），YAML 标准
```

## Playbook 6：launch 文件启动部分节点失败

### 症状

- launch 启动后部分节点未出现
- 报 `[ERROR] [launch]` 但其他节点继续运行
- 节点启动后立即退出

### 排查步骤

```bash
# 1. 用 debug 模式启动 launch，获取详细日志
ros2 launch <包名> <launch文件> --debug

# 2. 单独启动失败的节点（隔离问题）
ros2 run <包名> <节点名> --ros-args --log-level debug

# 3. 检查 launch 中的条件逻辑
# 查看 LaunchConfiguration / DeclareLaunchArgument 是否正确
ros2 launch <包名> <launch文件> --show-args

# 4. 检查节点是否因异常退出
# 在 launch 文件中添加 on_exit event handler：
```

```python
# launch 文件调试技巧
from launch.actions import RegisterEventHandler, LogInfo
from launch.event_handlers import OnProcessExit

# 捕获节点退出事件
RegisterEventHandler(
    OnProcessExit(
        target_action=my_node,
        on_exit=[
            LogInfo(msg="节点退出，返回码: "),
            LogInfo(msg=str(my_node.return_code)),
        ],
    )
)

# 设置 respawn 自动重启（调试时不建议，生产环境可用）
Node(
    package='my_pkg',
    executable='my_node',
    respawn=True,
    respawn_delay=2.0,
)
```

```bash
# 5. 检查是否有端口/资源冲突
ss -tlnp | grep <端口号>

# 6. 检查 ament index（确认包安装正确）
ros2 pkg prefix <包名>
ls $(ros2 pkg prefix <包名>)/share/<包名>/launch/
```

## Playbook 7：内存泄漏或 CPU 占用异常

### 症状

- 节点运行一段时间后内存持续增长
- CPU 占用远高于预期
- 系统变慢、其他节点响应延迟
- 最终 OOM 被系统杀死

### 排查步骤

```bash
# 1. 检查 ROS 2 daemon 是否异常（daemon 本身可能泄漏）
ros2 daemon status
ros2 daemon stop
ros2 daemon start

# 2. 监控进程资源占用
htop -p $(pgrep -d',' -f "ros2|controller|nav")
# 或单个节点
top -p $(pgrep -f <节点名>)

# 3. 查看进程内存详情
cat /proc/$(pgrep -f <节点名>)/status | grep -i vm

# 4. 使用 valgrind 检测内存泄漏（C++ 节点）
valgrind --leak-check=full --show-leak-kinds=all \
  ros2 run <包名> <节点名> 2>&1 | tee valgrind_output.txt

# 5. 检查是否有大量未处理的消息堆积
ros2 topic bw /scan
ros2 topic hz /scan
# 如果发布频率远高于处理频率，消息队列会膨胀

# 6. 检查是否有无限增长的容器（日志、缓存等）
# Python 节点：使用 tracemalloc 定位
# 在节点代码中临时加入：
# import tracemalloc; tracemalloc.start()
```

### 常见原因

- **消息队列无限增长**：QoS `depth` 设置过大或使用 `KEEP_ALL` 但消费速度跟不上
- **TF buffer 无限制**：`buffer_length` 设置过大或未设置
- **日志写入过多**：`RCLCPP_INFO` 在高频回调中打印
- **ros2 daemon 异常**：长期运行后 daemon 占用内存增长，定期重启 daemon
- **DDS 层资源泄漏**：特定 DDS 实现的已知问题，检查是否有可用补丁
- **Python 循环引用**：回调中持有对节点的强引用导致 GC 无法释放
