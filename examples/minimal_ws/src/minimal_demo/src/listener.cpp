/**
 * @file listener.cpp
 * @brief ROS 2 订阅者节点实现
 *
 * 本节点演示 ROS 2 订阅者的标准用法：
 *   - 继承 rclcpp::Node 并在构造函数中完成初始化
 *   - 使用 create_subscription() 创建话题订阅者
 *   - 使用 Lambda 或 std::bind 注册消息回调函数
 *
 * 订阅话题：/chatter (std_msgs/msg/String)
 */

#include <memory>
#include <string>

// ROS 2 核心头文件
#include "rclcpp/rclcpp.hpp"
// 标准字符串消息类型
#include "std_msgs/msg/string.hpp"

namespace minimal_demo
{

/**
 * @brief 订阅者节点类
 *
 * ListenerNode 监听 /chatter 话题，每收到一条消息就
 * 将消息内容打印到日志中。
 */
class ListenerNode : public rclcpp::Node
{
public:
  /**
   * @brief 构造函数：创建订阅者并注册回调
   */
  ListenerNode()
  : Node("listener_node")  // 节点名称：listener_node
  {
    RCLCPP_INFO(this->get_logger(), "订阅者节点已启动，等待 /chatter 消息...");

    // ----------------------------------------------------------
    // 创建订阅者
    // 话题名称：/chatter
    // 消息类型：std_msgs/msg/String
    // 队列深度（QoS history depth）：10
    // 回调函数：使用 Lambda 表达式捕获 this 指针
    // ----------------------------------------------------------
    subscription_ = this->create_subscription<std_msgs::msg::String>(
      "chatter",
      10,
      [this](const std_msgs::msg::String::SharedPtr msg) {
        this->topic_callback(msg);
      }
    );
  }

private:
  /**
   * @brief 消息回调函数
   *
   * 每次从 /chatter 话题收到消息时触发，将消息内容记录到日志。
   *
   * @param msg 收到的字符串消息（共享指针）
   */
  void topic_callback(const std_msgs::msg::String::SharedPtr msg)
  {
    RCLCPP_INFO(this->get_logger(), "收到: '%s'", msg->data.c_str());
  }

  // 订阅者对象（持有订阅的生命周期）
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr subscription_;
};

}  // namespace minimal_demo

// ============================================================
// main 入口函数
// ============================================================
int main(int argc, char * argv[])
{
  // 初始化 ROS 2 客户端库
  rclcpp::init(argc, argv);

  // 创建节点实例并进入事件循环
  // spin() 会持续处理消息回调，直到节点被关闭（Ctrl+C）
  rclcpp::spin(std::make_shared<minimal_demo::ListenerNode>());

  // 关闭 ROS 2 客户端库，释放资源
  rclcpp::shutdown();

  return 0;
}
