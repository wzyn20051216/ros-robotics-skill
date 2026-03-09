#ifndef MINIMAL_DEMO__TALKER_HPP_
#define MINIMAL_DEMO__TALKER_HPP_

// ROS 2 核心头文件
#include <rclcpp/rclcpp.hpp>
// 标准字符串消息类型
#include <std_msgs/msg/string.hpp>

// 标准库
#include <chrono>
#include <memory>
#include <string>

namespace minimal_demo
{

/**
 * @brief 发布者节点类
 *
 * TalkerNode 以固定频率（默认 1Hz）向 /chatter 话题发布
 * std_msgs/String 类型的消息。消息前缀可通过 ROS 2 参数配置。
 *
 * 参数：
 *   - message_prefix (string, 默认 "Hello")：消息内容的前缀字符串
 *
 * 发布话题：
 *   - /chatter (std_msgs/msg/String)：周期性字符串消息
 */
class TalkerNode : public rclcpp::Node
{
public:
  /**
   * @brief 构造函数
   * @param options 节点选项（可用于传入参数覆盖等）
   */
  explicit TalkerNode(const rclcpp::NodeOptions & options = rclcpp::NodeOptions());

  /**
   * @brief 析构函数（默认实现）
   */
  virtual ~TalkerNode() = default;

private:
  /**
   * @brief 定时器回调函数，每次触发时发布一条消息
   */
  void timer_callback();

  // 发布者：向 /chatter 发布字符串消息
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr publisher_;

  // 定时器：控制发布频率
  rclcpp::TimerBase::SharedPtr timer_;

  // 消息前缀（从参数服务器读取）
  std::string message_prefix_;

  // 消息计数器（从 0 开始累加）
  size_t count_;
};

}  // namespace minimal_demo

#endif  // MINIMAL_DEMO__TALKER_HPP_
