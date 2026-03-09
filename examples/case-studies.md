# 真实案例

## 案例 1：ROS 1 `catkin_ws` 构建失败

### 输入问题

用户反馈：`catkin_make` 总报依赖或链接错误，不确定该改 `package.xml` 还是 `CMakeLists.txt`。

### skill 的处理路径

1. 先运行 `scripts/detect_ros_workspace.py`
2. 再运行 `scripts/check_ros_workspace_consistency.py`
3. 加载 `references/ros1-catkin.md`
4. 优先对齐 `package.xml` 与 `CMakeLists.txt`

### 输出动作

- 标记缺失依赖
- 给出最小修复点
- 给出 `rosdep`、`catkin build` / `catkin_make` 的验证命令

## 案例 2：ROS 2 模型能加载，但 TF / RViz 不对

### 输入问题

用户反馈：RViz 能看到机器人，但方向错、传感器位置不对，导航也异常。

### skill 的处理路径

1. 加载 `references/robot-description-and-tf.md`
2. 核对 `robot_description`、`joint_states`、mesh 路径、Fixed Frame
3. 核对 `base_link`、`odom`、`map` 和传感器 frame

### 输出动作

- 指出可能错误的外参、关节轴或 frame 命名
- 给出最小复测链路
- 解释为什么应先修 TF，再看导航问题

## 案例 3：Nav2 已激活，但底盘不动

### 输入问题

用户反馈：规划正常、路径有了、Nav2 active，但车就是不走。

### skill 的处理路径

1. 加载 `references/navigation2.md`
2. 检查 `/cmd_vel` 是否生成
3. 检查底盘是否订阅到命令
4. 检查速度单位、QoS、急停和超时保护

### 输出动作

- 给出最可能的 3 个根因
- 每个根因给 1~2 个验证动作
- 给出底盘侧和导航侧的最小修改建议
