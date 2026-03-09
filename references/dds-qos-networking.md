# DDS / QoS / 网络配置参考

## 第一原则

ROS 2 通信问题大多出在 QoS 不兼容、DDS 发现机制和网络配置，而不是 ROS 2 本身有 bug。

---

## ROS_DOMAIN_ID

```bash
export ROS_DOMAIN_ID=42   # 不同 ID 的节点互不可见，推荐 0-101
```

同一网络多组机器人用不同 DOMAIN_ID 隔离。>101 在某些 DDS 实现中端口超范围。

---

## RMW 实现选择

| RMW | 包名 | 特点 |
|---|---|---|
| Fast DDS | `rmw_fastrtps_cpp` | 默认，功能全面 |
| Cyclone DDS | `rmw_cyclonedds_cpp` | 多机性能好，推荐生产环境 |
| Connext DDS | `rmw_connextdds` | 商业级，需许可证 |

```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
sudo apt install ros-jazzy-rmw-cyclonedds-cpp
```

---

## QoS Profile 常用组合

| 场景 | Reliability | Durability | History |
|---|---|---|---|
| 传感器 (LiDAR/Camera) | BestEffort | Volatile | KeepLast(5) |
| 控制指令 (cmd_vel) | Reliable | Volatile | KeepLast(1) |
| 地图/参数 | Reliable | TransientLocal | KeepLast(1) |
| TF 变换 | Reliable | Volatile | KeepLast(100) |

**不兼容规则：** Subscriber 不能比 Publisher 更严格。BestEffort 发布 + Reliable 订阅 = 无法通信。

---

## QoS 代码示例

### C++ (rclcpp)

```cpp
// 传感器 QoS
auto sensor_qos = rclcpp::QoS(rclcpp::KeepLast(5))
  .reliability(RMW_QOS_POLICY_RELIABILITY_BEST_EFFORT)
  .durability(RMW_QOS_POLICY_DURABILITY_VOLATILE);
auto scan_sub = node->create_subscription<sensor_msgs::msg::LaserScan>(
  "scan", sensor_qos, callback);

// 地图 QoS
auto map_qos = rclcpp::QoS(rclcpp::KeepLast(1))
  .reliability(RMW_QOS_POLICY_RELIABILITY_RELIABLE)
  .durability(RMW_QOS_POLICY_DURABILITY_TRANSIENT_LOCAL);
auto map_pub = node->create_publisher<nav_msgs::msg::OccupancyGrid>("map", map_qos);
```

### Python (rclpy)

```python
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy

sensor_qos = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    durability=DurabilityPolicy.VOLATILE,
    history=HistoryPolicy.KEEP_LAST, depth=5)

self.scan_sub = self.create_subscription(LaserScan, 'scan', self.cb, sensor_qos)
```

---

## 多机网络配置

基本要求：同一子网 + 同 DOMAIN_ID + 防火墙放行 UDP 7400-7500。

```bash
sudo ufw allow 7400:7500/udp
```

---

## CycloneDDS XML 配置

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CycloneDDS xmlns="https://cdds.io/config">
  <Domain>
    <General>
      <NetworkInterfaceAddress>enp0s3</NetworkInterfaceAddress>  <!-- 指定网卡 -->
    </General>
    <Discovery>
      <Peers>
        <Peer address="192.168.1.101"/>  <!-- 跨网段指定对端 -->
        <Peer address="192.168.1.102"/>
      </Peers>
    </Discovery>
  </Domain>
</CycloneDDS>
```

```bash
export CYCLONEDDS_URI=file:///path/to/cyclonedds.xml
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

---

## FastDDS Discovery Server

组播不可用时（Docker/VPN/跨网段）的替代方案：

```bash
# 服务端
fastdds discovery --server-id 0 --ip-address 192.168.1.100 --port 11811

# 客户端
export ROS_DISCOVERY_SERVER=192.168.1.100:11811
ros2 run demo_nodes_cpp talker

# CLI 工具需要 SUPER_CLIENT 模式才能发现节点
export FASTRTPS_DEFAULT_PROFILES_FILE=super_client.xml
```

---

## QoS 不兼容排查

```bash
ros2 doctor --report                    # 全面诊断
ros2 topic info /scan --verbose         # 查看 QoS 详情
```

| 症状 | 原因 | 修复 |
|---|---|---|
| `topic echo` 无输出但有发布者 | 默认 echo 用 Reliable，发布者 BestEffort | `ros2 topic echo /scan --qos-reliability best_effort` |
| 新节点收不到地图 | 发布者 Volatile | 改为 TransientLocal |
| 消息时有时无 | BestEffort + 网络丢包 | 改 Reliable 或优化网络 |

---

## 组播问题 (Docker/VPN/WSL)

```bash
docker run --network host ros:jazzy                   # Docker 用 host 模式
# WSL2: CycloneDDS 配置 Peers 为 localhost
# VPN 环境: 使用 FastDDS Discovery Server
```

---

## 官方与高星参考

- ROS 2 QoS: <https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Quality-of-Service-Settings.html>
- DDS 调优: <https://docs.ros.org/en/jazzy/How-To-Guides/DDS-tuning.html>
- CycloneDDS: <https://cyclonedds.io/docs/>
- FastDDS Discovery: <https://fast-dds.docs.eprosima.com/en/latest/fastdds/discovery/discovery_server.html>
- 多机通信: <https://docs.ros.org/en/jazzy/How-To-Guides/Multiple-Machines-Networking.html>
