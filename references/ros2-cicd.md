# ROS 2 CI/CD 最佳实践参考

## 第一原则

CI/CD 是保证 ROS 2 项目质量的关键。核心思路：**先跑通本地测试，再上 CI；先简单流水线，再逐步完善**。不要一开始就追求复杂的多阶段流水线，从一个能跑通 `colcon build && colcon test` 的 workflow 开始，逐步加入 lint、覆盖率、多平台支持。

## 本地测试基础

### colcon 测试命令

```bash
# 构建并运行所有测试
colcon build --cmake-args -DBUILD_TESTING=ON
colcon test
colcon test-result --verbose  # 查看详细测试结果

# 仅测试指定包
colcon test --packages-select my_robot_pkg
colcon test-result --verbose --test-result-base build/my_robot_pkg
```

### ament_cmake 测试集成（C++）

在 `CMakeLists.txt` 中添加测试：

```cmake
if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
  find_package(ament_cmake_pytest REQUIRED)

  # GTest 单元测试
  ament_add_gtest(test_motor_driver test/test_motor_driver.cpp)
  target_link_libraries(test_motor_driver motor_driver_lib)

  # 也可以用原生 CMake 方式
  add_test(NAME test_basic COMMAND test_motor_driver)

  # 在 C++ 包中运行 Python 测试
  ament_add_pytest_test(test_params test/test_params.py)
endif()
```

### ament_python 测试（Python 包）

在 `setup.cfg` 中配置 pytest：

```ini
[tool:pytest]
testpaths = test
```

在 `setup.py` 中声明测试依赖：

```python
tests_require=['pytest'],
```

### launch_testing 集成测试

用于测试节点间通信、完整启动流程等场景：

```python
import launch_testing
import unittest

def generate_test_description():
    return launch.LaunchDescription([
        Node(package='my_pkg', executable='my_node'),
        launch_testing.actions.ReadyToTest(),
    ])

class TestNodeStartup(unittest.TestCase):
    def test_node_is_running(self, proc_info):
        proc_info.assertWaitForStartup(process='my_node', timeout=10)
```

## GitHub Actions 完整模板

以下是一个可直接使用的 `.github/workflows/ros2-ci.yml`：

```yaml
name: ROS 2 CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        ros_distro: [humble, jazzy, rolling]
    container:
      image: ros:${{ matrix.ros_distro }}
    steps:
      - uses: actions/checkout@v4

      - name: 缓存 rosdep 依赖
        uses: actions/cache@v4
        with:
          path: /opt/ros/${{ matrix.ros_distro }}
          key: rosdep-${{ matrix.ros_distro }}-${{ hashFiles('**/package.xml') }}

      - name: 安装依赖
        run: |
          apt-get update
          rosdep update
          rosdep install --from-paths src --ignore-src -r -y

      - name: 构建
        run: |
          source /opt/ros/${{ matrix.ros_distro }}/setup.bash
          colcon build --cmake-args -DBUILD_TESTING=ON

      - name: 测试
        run: |
          source /opt/ros/${{ matrix.ros_distro }}/setup.bash
          source install/setup.bash
          colcon test
          colcon test-result --verbose

      - name: 上传测试结果
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results-${{ matrix.ros_distro }}
          path: build/*/test_results/
```

也可以使用 `ros-tooling` 提供的官方 Action 简化配置：

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        ros_distro: [humble, jazzy]
    steps:
      - uses: ros-tooling/setup-ros@v0.7
        with:
          required-ros-distributions: ${{ matrix.ros_distro }}
      - uses: ros-tooling/action-ros-ci@v0.3
        with:
          target-ros2-distro: ${{ matrix.ros_distro }}
          package-name: my_robot_pkg
```

## 代码质量检查

### ament_lint 工具集

在 `package.xml` 中添加测试依赖：

```xml
<test_depend>ament_lint_auto</test_depend>
<test_depend>ament_lint_common</test_depend>
```

在 `CMakeLists.txt` 中启用（会自动运行 cpplint、xmllint 等）：

```cmake
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()
```

常用的独立 lint 工具：

| 工具 | 用途 | 命令 |
|------|------|------|
| `ament_cpplint` | C++ 代码风格 | `ament_cpplint src/` |
| `ament_flake8` | Python PEP 8 | `ament_flake8 my_pkg/` |
| `ament_pep257` | Python 文档字符串 | `ament_pep257 my_pkg/` |
| `ament_xmllint` | XML 格式校验 | `ament_xmllint package.xml` |

## 测试覆盖率

### C++ 覆盖率（lcov / gcov）

```bash
# 构建时启用覆盖率标志
colcon build --cmake-args -DCMAKE_CXX_FLAGS="--coverage" -DCMAKE_C_FLAGS="--coverage"
colcon test

# 收集覆盖率数据
lcov --capture --directory build/ --output-file coverage.info
lcov --remove coverage.info '/usr/*' '/opt/*' --output-file coverage_filtered.info
genhtml coverage_filtered.info --output-directory coverage_html
```

### Python 覆盖率（pytest-cov）

```bash
python3 -m pytest --cov=my_pkg --cov-report=xml:coverage.xml test/
```

### CI 中集成 Codecov

```yaml
- name: 上传覆盖率到 Codecov
  uses: codecov/codecov-action@v4
  with:
    files: coverage.xml,coverage_filtered.info
    flags: unittests
    token: ${{ secrets.CODECOV_TOKEN }}
```

## 自动构建与发布

### bloom-release 发布流程

`bloom` 是 ROS 官方的发布工具，用于将包发布到 ROS 软件源：

```bash
bloom-release --track humble --rosdistro humble my_robot_pkg
```

### industrial_ci

`ros-industrial/industrial_ci` 提供了开箱即用的 CI 脚本：

```yaml
jobs:
  industrial_ci:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        ROS_DISTRO: [humble, jazzy]
    steps:
      - uses: actions/checkout@v4
      - uses: ros-industrial/industrial_ci@master
        env:
          ROS_DISTRO: ${{ matrix.ROS_DISTRO }}
          ADDITIONAL_DEBS: "lcov"
```

### Docker 化 CI

自定义 Dockerfile 适合有特殊依赖的项目：

```dockerfile
FROM ros:humble
RUN apt-get update && apt-get install -y ros-humble-navigation2 ros-humble-slam-toolbox
COPY . /ws/src/my_pkg
WORKDIR /ws
RUN . /opt/ros/humble/setup.sh && rosdep install --from-paths src -y && colcon build
CMD ["bash", "-c", ". install/setup.bash && colcon test && colcon test-result --verbose"]
```

## 多平台 CI

### Ubuntu 多版本矩阵

```yaml
strategy:
  matrix:
    include:
      - os: ubuntu-22.04
        ros_distro: humble
      - os: ubuntu-24.04
        ros_distro: jazzy
```

### aarch64 交叉编译（QEMU）

```yaml
- name: 设置 QEMU
  uses: docker/setup-qemu-action@v3
  with:
    platforms: arm64

- name: aarch64 构建测试
  run: |
    docker run --rm --platform linux/arm64 \
      ros:humble \
      bash -c "cd /ws && colcon build"
```

### Windows CI 注意事项

- 路径使用正斜杠或双反斜杠，避免转义问题
- 编码统一设为 UTF-8，避免中文路径乱码
- 部分 rosdep 包在 Windows 上无对应项，需用 `--skip-keys` 跳过
- 推荐使用 `choco install ros-humble-desktop` 安装 ROS 2

## 持续部署

### Docker 镜像自动构建推送

```yaml
- name: 构建并推送镜像
  uses: docker/build-push-action@v5
  with:
    push: true
    tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
    platforms: linux/amd64,linux/arm64
```

### 自动部署到机器人

```bash
# 通过 SSH + rsync 部署到目标机器
rsync -avz --delete install/ robot@192.168.1.100:/opt/robot_ws/install/
ssh robot@192.168.1.100 "sudo systemctl restart robot_bringup"
```

### 版本标签与 Release 自动化

```yaml
on:
  push:
    tags: ['v*']
jobs:
  release:
    steps:
      - uses: softprops/action-gh-release@v2
        with:
          files: build/*.deb
          generate_release_notes: true
```

## 常见故障

| 故障现象 | 原因分析 | 解决方案 |
|----------|----------|----------|
| `rosdep install` 失败 | 源列表未初始化或网络超时 | 运行 `rosdep init && rosdep update`，配置镜像源 |
| 测试在 CI 中超时 | 资源不足或依赖仿真环境 | 增加超时时间、使用 headless 模式、跳过 GPU 测试 |
| 不同发行版构建不兼容 | API 变更或依赖版本差异 | 使用条件编译、检查 `$ROS_DISTRO` 环境变量 |
| 缓存失效导致构建慢 | `package.xml` 变更触发缓存刷新 | 合理设计缓存 key，分层缓存 rosdep 和 colcon |
| `ament_lint` 报大量格式错误 | 未统一代码风格 | 添加 `.clang-format`、使用 pre-commit hooks |

## 推荐 CI 工具对比

| 特性 | GitHub Actions | GitLab CI | Jenkins | industrial_ci |
|------|---------------|-----------|---------|---------------|
| 配置复杂度 | 低 | 低 | 高 | 极低 |
| ROS 生态集成 | 好（有官方 Action） | 一般 | 一般 | 优秀 |
| 自托管 Runner | 支持 | 支持 | 必须 | 依赖宿主 CI |
| 多发行版矩阵 | 原生支持 | 原生支持 | 需插件 | 原生支持 |
| ARM 构建 | QEMU / 自托管 | QEMU / 自托管 | 自托管 | 依赖宿主 CI |
| 免费额度 | 2000 分钟/月 | 400 分钟/月 | 自建免费 | 免费 |
| 适用场景 | 开源项目首选 | 企业私有部署 | 大型团队定制 | 快速集成 |

## 官方与高星参考

- [ros-tooling/action-ros-ci](https://github.com/ros-tooling/action-ros-ci) - GitHub Actions 官方 ROS CI Action
- [ros-industrial/industrial_ci](https://github.com/ros-industrial/industrial_ci) - 工业级 ROS CI 方案
- [ROS 2 Testing Tutorial](https://docs.ros.org/en/rolling/Tutorials/Intermediate/Testing/Testing-Main.html) - 官方测试教程
- [bloom 文档](https://bloom.readthedocs.io/) - ROS 发布工具文档
- [colcon 文档](https://colcon.readthedocs.io/) - 构建工具参考
- [launch_testing](https://github.com/ros2/launch/tree/rolling/launch_testing) - 集成测试框架
