/**
 * @file talker.cpp
 * @brief ROS 2 发布者节点实现
 *
 * 本节点演示 ROS 2 发布者的标准用法：
 *   - 继承 rclcpp::Node 并在构造函数中完成初始化
 *   - 使用 declare_parameter() 声明并读取 ROS 2 参数
 *   - 使用 create_wall_timer() 创建固定频率定时器
 *   - 使用 create_publisher() 创建话题发布者
 *
 * 发布话题：/chatter (std_msgs/msg/String)，频率 1Hz
 * 参数：message_prefix (默认 "Hello")
 */

#include "minimal_demo/talker.hpp"

#include <chrono>
#include <memory>
#include <string>

// 使用 chrono 字面量（如 1000ms）
using namespace std::chrono_literals;

namespace minimal_demo
{

TalkerNode::TalkerNode(const rclcpp::NodeOptions & options)
: Node("talker_node", options),  // 节点名称：talker_node
  count_(0)                       // 消息计数器从 0 开始
{
  // ----------------------------------------------------------
  // 声明并读取参数
  // 若外部（launch 文件或命令行）未提供该参数，则使用默认值
  // ----------------------------------------------------------
  this->declare_parameter<std::string>("message_prefix", "Hello");
  message_prefix_ = this->get_parameter("message_prefix").as_string();

  RCLCPP_INFO(this->get_logger(),
    "发布者节点已启动，消息前缀: '%s'", message_prefix_.c_str());

  // ----------------------------------------------------------
  // 创建发布者
  // 话题名称：/chatter
  // 消息类型：std_msgs/msg/String
  // 队列深度（QoS history depth）：10
  // ----------------------------------------------------------
  publisher_ = this->create_publisher<std_msgs::msg::String>("chatter", 10);

  // ----------------------------------------------------------
  // 创建定时器，周期 1000ms（1Hz）
  // 每次触发时调用 timer_callback()
  // ----------------------------------------------------------
  timer_ = this->create_wall_timer(
    1000ms,
    std::bind(&TalkerNode::timer_callback, this));
}

void TalkerNode::timer_callback()
{
  // 构建消息内容
  auto message = std_msgs::msg::String();
  message.data = message_prefix_ +
    " ROS 2 minimal demo - count: " +
    std::to_string(count_++);

  // 打印日志（INFO 级别）
  RCLCPP_INFO(this->get_logger(), "发布: '%s'", message.data.c_str());

  // 发布消息到 /chatter 话题
  publisher_->publish(message);
}

}  // namespace minimal_demo

// ============================================================
// main 入口函数
// ============================================================
int main(int argc, char * argv[])
{
  // 初始化 ROS 2 客户端库
  rclcpp::init(argc, argv);

  // 创建节点实例并进入事件循环
  // spin() 会阻塞，直到节点被关闭（Ctrl+C）
  rclcpp::spin(std::make_shared<minimal_demo::TalkerNode>());

  // 关闭 ROS 2 客户端库，释放资源
  rclcpp::shutdown();

  return 0;
}
