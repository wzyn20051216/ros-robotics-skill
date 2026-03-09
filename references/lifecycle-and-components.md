# Lifecycle 节点与组件化参考

## 第一原则

Lifecycle 和组件化是 ROS 2 进阶模式，不要为了用而用。先确认：是否需要状态管理（硬件初始化/释放）？是否需要进程内零拷贝通信？简单 pub/sub 用普通 `rclcpp::Node` 即可。

---

## Lifecycle 状态转换

```
  create → [Unconfigured] --on_configure→ [Inactive] --on_activate→ [Active]
                                             ↑ on_deactivate ←────────┘
           on_cleanup ↓                      on_shutdown ↓
                  [Unconfigured]                    [Finalized]
```

| 回调 | 用途 | 示例 |
|---|---|---|
| `on_configure` | 读参数、初始化硬件、创建 pub/sub | 连接串口 |
| `on_activate` | 启动数据流、使能硬件 | 开始发布传感器数据 |
| `on_deactivate` | 暂停数据流 | 停止电机输出 |
| `on_cleanup` | 释放资源 | 关闭文件句柄 |
| `on_shutdown` | 最终清理 | 断开硬件 |

---

## Lifecycle 代码示例 (C++)

```cpp
#include <rclcpp_lifecycle/lifecycle_node.hpp>
#include <sensor_msgs/msg/laser_scan.hpp>

class LidarDriverNode : public rclcpp_lifecycle::LifecycleNode {
public:
  explicit LidarDriverNode(const rclcpp::NodeOptions & options)
  : LifecycleNode("lidar_driver", options) {}

  CallbackReturn on_configure(const rclcpp_lifecycle::State &) override {
    port_ = declare_parameter("port", "/dev/ttyUSB0");
    scan_pub_ = create_publisher<sensor_msgs::msg::LaserScan>("scan", 10);
    RCLCPP_INFO(get_logger(), "已配置，端口: %s", port_.c_str());
    return CallbackReturn::SUCCESS;
  }

  CallbackReturn on_activate(const rclcpp_lifecycle::State &) override {
    timer_ = create_wall_timer(std::chrono::milliseconds(100),
      [this]() { /* 从硬件读取并发布 */ });
    return CallbackReturn::SUCCESS;
  }

  CallbackReturn on_deactivate(const rclcpp_lifecycle::State &) override {
    timer_.reset();
    return CallbackReturn::SUCCESS;
  }

  CallbackReturn on_cleanup(const rclcpp_lifecycle::State &) override {
    scan_pub_.reset();
    return CallbackReturn::SUCCESS;
  }

  CallbackReturn on_shutdown(const rclcpp_lifecycle::State &) override {
    timer_.reset(); scan_pub_.reset();
    return CallbackReturn::SUCCESS;
  }

private:
  std::string port_;
  rclcpp_lifecycle::LifecyclePublisher<sensor_msgs::msg::LaserScan>::SharedPtr scan_pub_;
  rclcpp::TimerBase::SharedPtr timer_;
};
```

---

## 命令行管理

```bash
ros2 lifecycle nodes                          # 列出所有 lifecycle 节点
ros2 lifecycle get /lidar_driver              # 查看当前状态
ros2 lifecycle set /lidar_driver configure    # 触发转换
ros2 lifecycle set /lidar_driver activate
ros2 lifecycle set /lidar_driver deactivate
ros2 lifecycle list /lidar_driver             # 查看可用转换
```

---

## 组件化 (rclcpp_components)

### 注册组件

```cpp
#include <rclcpp_components/register_node_macro.hpp>
RCLCPP_COMPONENTS_REGISTER_NODE(my_package::MyNode)
```

### CMakeLists.txt

```cmake
find_package(rclcpp_components REQUIRED)

add_library(my_node_component SHARED src/my_node.cpp)
ament_target_dependencies(my_node_component rclcpp rclcpp_components sensor_msgs)

rclcpp_components_register_node(my_node_component
  PLUGIN "my_package::MyNode"
  EXECUTABLE my_node_exe)

install(TARGETS my_node_component ARCHIVE DESTINATION lib LIBRARY DESTINATION lib)
```

---

## 容器化运行

```bash
ros2 run rclcpp_components component_container                         # 启动容器
ros2 component load /ComponentManager my_package my_package::MyNode   # 加载组件
ros2 component list                                                    # 查看已加载
```

### Launch 文件

```python
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode

container = ComposableNodeContainer(
    name='my_container', namespace='', package='rclcpp_components',
    executable='component_container',
    composable_node_descriptions=[
        ComposableNode(package='my_package', plugin='my_package::LidarProcessor',
                       name='lidar_proc', parameters=[{'use_sim_time': True}]),
        ComposableNode(package='my_package', plugin='my_package::PointCloudFilter',
                       name='pc_filter'),  # 同容器 = 进程内零拷贝
    ])
```

**零拷贝条件：** 同一容器内 + `unique_ptr` 发布 + 订阅端用智能指针回调。

---

## 故障恢复

```cpp
CallbackReturn on_configure(const rclcpp_lifecycle::State &) override {
  try {
    hardware_ = connect_hardware(port_);
  } catch (const std::exception & e) {
    RCLCPP_ERROR(get_logger(), "硬件连接失败: %s", e.what());
    return CallbackReturn::FAILURE;  // 保持 Unconfigured
  }
  return CallbackReturn::SUCCESS;
}
```

Bond 机制（Nav2 使用）可检测节点存活，上层管理器在节点崩溃时自动恢复。

---

## 常见故障

| 现象 | 原因 | 排查 |
|---|---|---|
| configure 超时 | 回调中阻塞操作 | 阻塞操作移到线程 |
| 组件 PluginNotFound | 插件名拼写错误 | `ros2 component types` 查看可用名 |
| 进程内通信未生效 | QoS 不匹配或未用 unique_ptr | 检查 QoS + 发布方式 |
| 节点卡在 inactive | activate 回调返回 FAILURE | 检查日志错误信息 |

---

## 官方与高星参考

- Lifecycle 设计文档: <https://design.ros2.org/articles/node_lifecycle.html>
- Composition 教程: <https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Composition.html>
- rclcpp_lifecycle API: <https://docs.ros.org/en/jazzy/p/rclcpp_lifecycle/>
- nav2_lifecycle_manager: <https://github.com/ros-navigation/navigation2/tree/main/nav2_lifecycle_manager>
