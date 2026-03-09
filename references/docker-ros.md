# Docker 容器化 ROS 开发参考

## 第一原则

> Docker 解决的是环境一致性问题，不要把容器当虚拟机用。
> 把构建步骤写进 Dockerfile，而不是手动进容器装东西。

## 官方 ROS Docker 镜像

| 镜像 Tag | 内容 | 用途 |
|----------|------|------|
| `osrf/ros:humble-desktop` | Humble + RViz + 工具 | 开发、可视化 |
| `osrf/ros:humble-ros-base` | Humble 最小运行时 | 部署、CI |
| `osrf/ros:jazzy-desktop` | Jazzy 完整桌面 | 最新版开发 |

Tag 命名规则：`{distro}-{variant}`，variant 包括 `ros-core`（最小）、`ros-base`（基础）、`desktop`（完整）。

## 基础使用

```bash
# 启动 ROS 2 容器（host 网络模式最简单，DDS 发现无障碍）
docker run -it --rm --network host osrf/ros:humble-desktop bash

# 挂载本地工作区
docker run -it --rm --network host \
  -v ~/ros2_ws:/root/ros2_ws \
  osrf/ros:humble-desktop bash
```

## 多阶段构建 Dockerfile 模板

```dockerfile
# === 阶段 1: 基础依赖 ===
FROM osrf/ros:humble-ros-base AS base
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-colcon-common-extensions \
    ros-humble-nav2-bringup \
    && rm -rf /var/lib/apt/lists/*

# === 阶段 2: 编译 ===
FROM base AS build
WORKDIR /ros2_ws
COPY src/ src/
RUN apt-get update && rosdep update && \
    rosdep install --from-paths src --ignore-src -r -y && \
    rm -rf /var/lib/apt/lists/*
RUN . /opt/ros/humble/setup.sh && \
    colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release

# === 阶段 3: 运行时（只保留编译产物）===
FROM osrf/ros:humble-ros-base AS runtime
COPY --from=build /ros2_ws/install /ros2_ws/install
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["ros2", "launch", "my_robot", "bringup.launch.py"]
```

```bash
#!/bin/bash
# entrypoint.sh
set -e
source /opt/ros/humble/setup.bash
source /ros2_ws/install/setup.bash
exec "$@"
```

## GUI 显示（X11 转发）

```bash
# Linux 主机
xhost +local:docker
docker run -it --rm --network host \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  --device /dev/dri:/dev/dri \
  osrf/ros:humble-desktop rviz2
xhost -local:docker
```

## 开发容器 vs 部署容器

| 特性 | 开发容器 | 部署容器 |
|------|---------|---------|
| 源码 | Volume 挂载，实时编辑 | COPY 到镜像内 |
| 工具 | 安装 vim、gdb 等 | 最小化 |
| 构建 | 容器内 colcon build | 多阶段构建 |
| 运行 | `docker run -it` 交互 | `docker run -d` 后台 |

## docker-compose 多节点编排

```yaml
# docker-compose.yml
version: "3.8"
services:
  robot_base:
    image: my_robot:humble
    build: { context: ., dockerfile: Dockerfile }
    network_mode: host
    privileged: true
    devices: ["/dev/ttyUSB0:/dev/ttyUSB0"]
    environment: { ROS_DOMAIN_ID: "42" }
    command: ros2 launch my_robot base_driver.launch.py

  slam:
    image: my_robot:humble
    network_mode: host
    environment: { ROS_DOMAIN_ID: "42" }
    depends_on: [robot_base]
    command: ros2 launch slam_toolbox online_async_launch.py

  navigation:
    image: my_robot:humble
    network_mode: host
    environment: { ROS_DOMAIN_ID: "42" }
    depends_on: [robot_base, slam]
    volumes: ["./maps:/maps:ro"]
    command: ros2 launch nav2_bringup navigation_launch.py map:=/maps/my_map.yaml
```

```bash
docker compose up -d          # 启动所有服务
docker compose logs -f slam   # 查看日志
docker compose down           # 停止
```

## DDS 与容器网络

`--network host` 最简单，DDS 直接可用。必须用 bridge 时，配置 CycloneDDS 单播：

```xml
<!-- cyclonedds.xml -->
<CycloneDDS>
  <Domain>
    <General>
      <AllowMulticast>false</AllowMulticast>
    </General>
    <Discovery>
      <Peers>
        <Peer address="robot_base"/>
        <Peer address="slam"/>
      </Peers>
    </Discovery>
  </Domain>
</CycloneDDS>
```

```bash
export CYCLONEDDS_URI=file:///config/cyclonedds.xml
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

## 常见故障

| 现象 | 可能原因 | 解决方法 |
|------|---------|---------|
| 容器间节点找不到 | 网络模式/DDS 配置 | 优先用 `--network host` |
| GUI 无法显示 | DISPLAY/权限 | `xhost +local:docker` |
| 编译缓存失效 | Dockerfile 层顺序 | `COPY src/` 放在依赖安装之后 |
| 容器内找不到设备 | 缺 `--privileged` | 添加 `--device` 映射 |

## 官方与高星参考

- [OSRF Docker Images](https://hub.docker.com/r/osrf/ros)
- [ROS 2 Docker 教程](https://docs.ros.org/en/humble/How-To-Guides/Run-2-Nodes-in-Docker.html)
- [VS Code Dev Containers + ROS](https://github.com/athackst/vscode_ros2_workspace)
