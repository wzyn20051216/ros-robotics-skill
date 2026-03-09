# micro-ROS 与嵌入式协同

## 何时使用 `micro-ROS`

当 MCU 必须直接成为 ROS 2 计算图中的节点时，再考虑 `micro-ROS`。

如果 MCU 只是底盘、传感器或执行器控制器，很多场景下 **Linux 侧桥接节点 + 自定义串口 / CAN 协议** 更简单、更稳、更容易调试。

## 板端原则

- 优先静态内存
- ISR 中不做阻塞、复杂序列化、动态分配
- 明确消息时间戳来源和失连重连策略
- 对底盘 / 执行器必须实现超时保护、急停和看门狗

## 接口约定

至少明确：

- 传输介质：UART / CAN / USB / Ethernet
- 帧格式、字节序、校验、超时、重传
- 时间源和同步方式
- 速度、角速度、里程计、姿态的单位与缩放关系

## 官方参考

- micro-ROS：<https://micro.ros.org/docs/overview/introduction/>
