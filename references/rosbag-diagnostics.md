# rosbag2 录制回放与诊断参考

## 第一原则

rosbag 是 ROS 调试核心工具。先录后分析，不要凭感觉猜问题，让数据说话。

---

## ros2 bag record 录制

```bash
ros2 bag record -a                                              # 录制所有 topic
ros2 bag record /scan /odom /cmd_vel /tf /tf_static             # 指定 topic
ros2 bag record -o my_bag /scan /odom                           # 指定输出目录
ros2 bag record --regex "/camera/.*"                            # 正则匹配
ros2 bag record -a --exclude "/camera/image_raw"                # 排除 topic

# 压缩与格式
ros2 bag record -a -s mcap --compression-mode file --compression-format zstd
ros2 bag record -a --max-bag-size 1073741824                    # 按 1GB 自动分割

# 现场录制模板
ros2 bag record -s mcap --compression-mode file --compression-format zstd \
  -o $(date +%Y%m%d_%H%M%S)_field /scan /odom /tf /tf_static /cmd_vel /imu/data
```

---

## ros2 bag play 回放

```bash
ros2 bag play my_bag/                           # 基础回放
ros2 bag play my_bag/ --rate 2.0                # 2 倍速
ros2 bag play my_bag/ --rate 0.5                # 慢速
ros2 bag play my_bag/ --loop                    # 循环
ros2 bag play my_bag/ --start-offset 10.0       # 跳过前 10 秒
ros2 bag play my_bag/ --remap /cmd_vel:=/cmd_vel_recorded  # remap
ros2 bag play my_bag/ --clock                   # 发布仿真时钟
ros2 bag play my_bag/ --start-paused            # 暂停启动，空格继续
ros2 bag play my_bag/ --topics /scan /odom      # 只回放指定 topic
```

---

## ros2 bag info

```bash
ros2 bag info my_bag/
# 输出: 文件大小、存储格式、时长、消息数、topic 列表及各 topic 消息计数
```

---

## mcap 格式优势

| 特性 | sqlite3 (旧默认) | mcap (推荐) |
|---|---|---|
| 写入性能 | 中等 | 高（追加写入） |
| 读取性能 | 全表扫描 | 索引随机访问 |
| 文件恢复 | 损坏难恢复 | 部分损坏可恢复 |
| 工具链 | ROS 原生 | Foxglove Studio 原生支持 |
| 压缩 | 有限 | zstd/lz4 per-chunk |

```bash
pip install mcap-cli
mcap info my_bag_0.mcap
mcap filter my_bag_0.mcap --start 1709971800000000000 --end 1709971860000000000 -o trimmed.mcap
mcap filter input.mcap --include-topic /scan -o filtered.mcap
```

---

## 离线调试工作流

```bash
# 1. 现场录制
ros2 bag record -s mcap -o field_data /scan /odom /tf /tf_static /cmd_vel

# 2. 查看信息
ros2 bag info field_data/

# 3. 回放 + 可视化（三个终端）
ros2 bag play field_data/ --clock --rate 0.5
ros2 run rviz2 rviz2 --ros-args -p use_sim_time:=true
ros2 run rqt_plot rqt_plot /odom/twist/twist/linear/x

# 4. 修复代码后再回放验证
ros2 bag play field_data/ --clock
```

---

## 诊断工具

```bash
# ros2 doctor
ros2 doctor --report     # 完整报告（网络/RMW/QoS）
ros2 doctor              # 只看警告和错误

# rqt 工具集
ros2 run rqt_graph rqt_graph       # 节点连接图
ros2 run rqt_console rqt_console   # 日志查看
ros2 run rqt_plot rqt_plot         # 数值曲线

# topic 诊断
ros2 topic hz /scan                # 发布频率
ros2 topic delay /scan             # 消息延迟
ros2 topic bw /scan                # 带宽
ros2 topic info /scan --verbose    # QoS 详情
ros2 node info /my_node            # 节点详情
```

---

## 常见问题

| 现象 | 原因 | 解决 |
|---|---|---|
| bag 文件过大 | 高频大数据 topic | 用 zstd 压缩 + 过滤不必要 topic |
| 回放收不到数据 | QoS 不匹配 | 用 `--qos-profile-overrides-path` |
| TF extrapolation error | 未用 `--clock` | 回放加 `--clock`，节点设 `use_sim_time:=true` |
| 回放顺序混乱 | 时间戳不同步 | 确认各 topic 用同一时钟源 |
| sqlite3 bag 损坏 | 录制时断电 | 迁移到 mcap 格式 |

### QoS 覆盖配置 (qos.yaml)

```yaml
/scan:
  reliability: best_effort
  durability: volatile
  history: keep_last
  depth: 5
/map:
  reliability: reliable
  durability: transient_local
  history: keep_last
  depth: 1
```

```bash
ros2 bag play my_bag/ --qos-profile-overrides-path qos.yaml
```

---

## 官方与高星参考

- ros2 bag CLI: <https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Recording-And-Playing-Back-Data.html>
- rosbag2 GitHub: <https://github.com/ros2/rosbag2>
- mcap 文档: <https://mcap.dev/>
- Foxglove Studio: <https://foxglove.dev/>
- ros2 doctor: <https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Getting-Started-With-Ros2doctor.html>
