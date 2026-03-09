#!/usr/bin/env python3
"""! @brief 检测 ROS 工作区类型并给出建议命令。"""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class PackageInfo:
    """! @brief 单个 package 的识别结果。"""

    name: str
    path: str
    build_type: str
    markers: list[str]


@dataclass
class DetectionResult:
    """! @brief 工作区识别结果。"""

    workspace: str
    workspace_type: str
    markers: list[str]
    package_count: int
    ros1_packages: int
    ros2_packages: int
    unknown_packages: int
    recommended_commands: list[str]
    packages: list[PackageInfo]


def read_text_if_exists(path: Path) -> str:
    """! @brief 读取文本文件；失败时返回空串。"""
    try:
        return path.read_text(encoding='utf-8', errors='ignore')
    except OSError:
        return ''


def looks_like_ament_python(setup_py_text: str) -> bool:
    """! @brief 粗略判断 `setup.py` 是否更像 ament_python 包。"""
    return 'share/ament_index/resource_index/packages' in setup_py_text or 'ament_index' in setup_py_text


def parse_package_xml(path: Path) -> tuple[str | None, set[str]]:
    """! @brief 从 `package.xml` 提取包名与 buildtool 依赖；失败时返回空结果。"""
    try:
        tree = ET.parse(path)
    except ET.ParseError:
        return None, set()
    root = tree.getroot()
    name_node = root.find('name')
    package_name = name_node.text.strip() if name_node is not None and name_node.text else None
    buildtool_depends: set[str] = set()
    for node in root.findall('buildtool_depend'):
        if node.text and node.text.strip():
            buildtool_depends.add(node.text.strip())
    return package_name, buildtool_depends


def detect_package(package_xml: Path) -> PackageInfo:
    """! @brief 根据 `package.xml` 与构建文件判断包类型。"""
    package_dir = package_xml.parent
    xml_text = read_text_if_exists(package_xml)
    cmake_text = read_text_if_exists(package_dir / 'CMakeLists.txt')
    setup_py_text = read_text_if_exists(package_dir / 'setup.py')
    package_name, buildtool_depends = parse_package_xml(package_xml)
    markers: list[str] = []

    ros1_hits = 0
    ros2_hits = 0

    if 'catkin' in buildtool_depends:
        ros1_hits += 2
        markers.append('package.xml:catkin')
    if 'find_package(catkin' in cmake_text or 'catkin_package(' in cmake_text:
        ros1_hits += 2
        markers.append('cmake:catkin')

    if {'ament_cmake', 'ament_python'} & buildtool_depends:
        ros2_hits += 2
        markers.append('package.xml:ament')
    if 'find_package(ament_cmake' in cmake_text or 'ament_package(' in cmake_text:
        ros2_hits += 2
        markers.append('cmake:ament')
    if 'ament_python' in xml_text or looks_like_ament_python(setup_py_text):
        ros2_hits += 1
        markers.append('python:ament-pattern')

    if ros1_hits > 0 and ros2_hits == 0:
        build_type = 'ros1-catkin'
    elif ros2_hits > 0 and ros1_hits == 0:
        build_type = 'ros2-colcon'
    elif ros1_hits > 0 and ros2_hits > 0:
        build_type = 'mixed-signals'
    else:
        build_type = 'unknown'

    return PackageInfo(package_name or package_dir.name, str(package_dir), build_type, markers)


def iter_package_xml_files(root: Path) -> Iterable[Path]:
    """! @brief 遍历工作区中的 `package.xml`。"""
    ignored = {'build', 'devel', 'install', 'log', '.git', '.svn', '.idea', '__pycache__'}
    for path in root.rglob('package.xml'):
        if any(part in ignored for part in path.parts):
            continue
        yield path


def detect_workspace(root: Path) -> DetectionResult:
    """! @brief 检测工作区类型并返回建议。"""
    markers: list[str] = []
    packages = [detect_package(path) for path in iter_package_xml_files(root)]
    src_cmake = root / 'src' / 'CMakeLists.txt'
    if src_cmake.exists():
        markers.append('workspace:src/CMakeLists.txt')
    if (root / '.catkin_tools').exists():
        markers.append('workspace:.catkin_tools')
    if (root / 'devel').exists():
        markers.append('workspace:devel')
    if (root / 'install').exists():
        markers.append('workspace:install')
    if (root / 'colcon.meta').exists():
        markers.append('workspace:colcon.meta')

    ros1_packages = sum(1 for item in packages if item.build_type == 'ros1-catkin')
    ros2_packages = sum(1 for item in packages if item.build_type == 'ros2-colcon')
    unknown_packages = sum(1 for item in packages if item.build_type == 'unknown')

    if src_cmake.exists() and ros1_packages > 0 and ros2_packages == 0:
        workspace_type = 'ros1-catkin'
    elif ros2_packages > 0 and ros1_packages == 0:
        workspace_type = 'ros2-colcon'
    elif ros1_packages > 0 and ros2_packages > 0:
        workspace_type = 'mixed'
    elif src_cmake.exists():
        workspace_type = 'ros1-catkin'
    else:
        workspace_type = 'unknown'

    if workspace_type == 'ros1-catkin':
        recommended_commands = [
            'source /opt/ros/$ROS_DISTRO/setup.bash',
            'rosdep install --from-paths src --ignore-src -r -y',
            'catkin build    # 若项目使用 catkin_tools',
            'catkin_make     # 若项目历史上使用 catkin_make',
            'source devel/setup.bash',
        ]
    elif workspace_type == 'ros2-colcon':
        recommended_commands = [
            'source /opt/ros/$ROS_DISTRO/setup.bash',
            'rosdep install --from-paths src --ignore-src -r -y',
            'colcon build',
            'source install/setup.bash',
            'colcon test && colcon test-result --verbose',
        ]
    elif workspace_type == 'mixed':
        recommended_commands = [
            '先识别每个 package 的构建系统，不要一刀切迁移',
            '优先读取 references/interop-and-migration.md',
            '分别 source 对应环境，并验证桥接边界',
        ]
    else:
        recommended_commands = ['未识别到明确工作区类型，请先检查 package.xml、CMakeLists.txt、setup.py 与构建脚本']

    return DetectionResult(str(root), workspace_type, markers, len(packages), ros1_packages, ros2_packages, unknown_packages, recommended_commands, packages)


def print_human_readable(result: DetectionResult) -> None:
    """! @brief 输出人类可读结果。"""
    print(f'workspace: {result.workspace}')
    print(f'workspace_type: {result.workspace_type}')
    print(f'package_count: {result.package_count}')
    print(f'ros1_packages: {result.ros1_packages}')
    print(f'ros2_packages: {result.ros2_packages}')
    print(f'unknown_packages: {result.unknown_packages}')
    if result.markers:
        print('markers:')
        for marker in result.markers:
            print(f'  - {marker}')
    print('recommended_commands:')
    for command in result.recommended_commands:
        print(f'  - {command}')
    print('packages:')
    for package in result.packages:
        marker_text = ', '.join(package.markers) if package.markers else 'none'
        print(f'  - {package.name}: {package.build_type} [{marker_text}]')


def main() -> None:
    """! @brief CLI 入口。"""
    parser = argparse.ArgumentParser(description='检测 ROS 工作区类型')
    parser.add_argument('path', nargs='?', default='.', help='工作区根目录，默认当前目录')
    parser.add_argument('--json', action='store_true', help='以 JSON 输出')
    args = parser.parse_args()
    root = Path(args.path).resolve()
    result = detect_workspace(root)
    if args.json:
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        return
    print_human_readable(result)


if __name__ == '__main__':
    main()
