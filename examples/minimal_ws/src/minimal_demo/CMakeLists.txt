cmake_minimum_required(VERSION 3.8)
project(minimal_demo)

# 启用严格编译警告（ROS 2 最佳实践）
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# ============================================================
# 查找依赖包
# ============================================================
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)

# ============================================================
# 包含目录（头文件路径）
# ============================================================
include_directories(include)

# ============================================================
# 编译目标：talker（发布者节点）
# ============================================================
add_executable(talker src/talker.cpp)
ament_target_dependencies(talker
  rclcpp
  std_msgs
)

# ============================================================
# 编译目标：listener（订阅者节点）
# ============================================================
add_executable(listener src/listener.cpp)
ament_target_dependencies(listener
  rclcpp
  std_msgs
)

# ============================================================
# 安装规则：可执行文件
# ============================================================
install(TARGETS
  talker
  listener
  DESTINATION lib/${PROJECT_NAME}
)

# ============================================================
# 安装规则：launch 文件和配置文件
# ============================================================
install(DIRECTORY
  launch
  config
  DESTINATION share/${PROJECT_NAME}
)

# ============================================================
# 安装规则：头文件
# ============================================================
install(DIRECTORY
  include/
  DESTINATION include
)

# ============================================================
# 测试配置（可选，保留标准结构）
# ============================================================
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # 跳过版权检查（示例代码）
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

# ============================================================
# 导出功能包信息（必须放在最后）
# ============================================================
ament_package()
