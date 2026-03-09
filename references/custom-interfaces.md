# 自定义 msg/srv/action 参考

## 第一原则

> 自定义接口是 ROS 通信的基础，接口定义要稳定、语义清晰、向后兼容。
> 一旦接口被多个包使用，修改代价极高。设计时多花五分钟，维护时少花五小时。

## .msg 文件语法

基本类型：`bool`、`float32`、`float64`、`int32`、`string` 等。支持固定数组 `float64[3]`、动态数组 `string[]`、常量、嵌套消息。

```
# DetectedObject.msg
uint8 CLASS_PERSON = 1
uint8 CLASS_CAR = 2
std_msgs/Header header
string label
uint8 class_id
float32 confidence
geometry_msgs/Pose pose
float64[3] dimensions           # 固定长度 [长, 宽, 高]
string[] tags                   # 动态长度
```

## .srv 文件语法

请求和响应用 `---` 分隔：

```
# GetObjectInfo.srv
string object_id
---
bool success
string message
geometry_msgs/Pose pose
```

## .action 文件语法

Goal / Result / Feedback 三段式，两个 `---` 分隔：

```
# NavigateToObject.action
string object_id
float64 approach_distance
---
bool success
geometry_msgs/PoseStamped final_pose
---
float64 distance_remaining
uint8 navigation_status         # 0=行进 1=避障 2=重规划
```

## 包结构与 CMakeLists.txt 配置

目录结构：`my_interfaces/{msg/, srv/, action/, CMakeLists.txt, package.xml}`

```cmake
cmake_minimum_required(VERSION 3.8)
project(my_interfaces)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/DetectedObject.msg"
  "msg/ObjectArray.msg"
  "srv/GetObjectInfo.srv"
  "action/NavigateToObject.action"
  DEPENDENCIES std_msgs geometry_msgs sensor_msgs
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
```

## package.xml 配置

```xml
<?xml version="1.0"?>
<package format="3">
  <name>my_interfaces</name>
  <version>0.1.0</version>
  <description>自定义消息、服务和 Action 接口定义</description>
  <license>Apache-2.0</license>

  <buildtool_depend>ament_cmake</buildtool_depend>
  <buildtool_depend>rosidl_default_generators</buildtool_depend>
  <depend>std_msgs</depend>
  <depend>geometry_msgs</depend>
  <depend>sensor_msgs</depend>
  <exec_depend>rosidl_default_runtime</exec_depend>
  <member_of_group>rosidl_interface_packages</member_of_group>

  <export><build_type>ament_cmake</build_type></export>
</package>
```

## 跨包引用

在其他包中使用自定义接口，CMakeLists.txt 添加：

```cmake
find_package(my_interfaces REQUIRED)
ament_target_dependencies(my_node rclcpp my_interfaces)
```

package.xml 添加 `<depend>my_interfaces</depend>`。

## 生成顺序问题

接口包必须在依赖它的功能包之前编译：

```bash
colcon build --packages-select my_interfaces          # 先编译接口包
colcon build --packages-select my_robot_node          # 再编译功能包
colcon build --packages-up-to my_robot_node           # 或自动按依赖顺序编译
```

## Python / C++ 中使用

```python
# Python
from my_interfaces.msg import DetectedObject
msg = DetectedObject()
msg.label = 'person'
msg.class_id = DetectedObject.CLASS_PERSON
msg.confidence = 0.95
self.create_publisher(DetectedObject, '/detections', 10).publish(msg)
```

```cpp
// C++ - 注意头文件用蛇形命名：DetectedObject → detected_object.hpp
#include "my_interfaces/msg/detected_object.hpp"
using DetectedObject = my_interfaces::msg::DetectedObject;
auto msg = DetectedObject();
msg.label = "person";
msg.class_id = DetectedObject::CLASS_PERSON;
node->create_publisher<DetectedObject>("/detections", 10)->publish(msg);
```

## 版本兼容和字段演进策略

| 操作 | 安全性 | 说明 |
|------|--------|------|
| 末尾添加字段（带默认值） | 安全 | 旧代码忽略新字段 |
| 删除字段 | 不安全 | 旧代码访问已删字段报错 |
| 重排字段顺序 | 不安全 | 二进制序列化依赖顺序 |
| 修改字段类型 | 不安全 | 反序列化失败 |

策略：小改动在末尾加字段；大变更创建新类型（如 `DetectedObjectV2.msg`）。

## 常见故障

| 现象 | 可能原因 | 解决方法 |
|------|---------|---------|
| 编译报找不到包 | `package.xml` 未声明依赖 | 添加 `<depend>my_interfaces</depend>` |
| 接口文件找不到 | 接口包未先编译 | `colcon build --packages-up-to` |
| 运行时类型不匹配 | rebuild 后未 source | `source install/setup.bash` |
| Python ImportError | 包未安装或路径错 | 确认 build 成功且已 source |

```bash
# 调试常用命令
ros2 interface list                                    # 列出所有接口
ros2 interface show my_interfaces/msg/DetectedObject   # 查看定义
ros2 interface proto my_interfaces/msg/DetectedObject  # 查看默认值
```

## 官方与高星参考

- [ROS 2 自定义接口教程](https://docs.ros.org/en/humble/Tutorials/Beginner-Client-Libraries/Custom-ROS2-Interfaces.html)
- [rosidl 文档](https://docs.ros.org/en/humble/Concepts/About-Internal-Interfaces.html)
- [common_interfaces 包](https://github.com/ros2/common_interfaces)
