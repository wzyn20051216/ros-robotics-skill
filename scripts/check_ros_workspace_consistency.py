#!/usr/bin/env python3
"""! @brief 检查 ROS 工作区里依赖声明与安装规则的一致性。"""

from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path

IGNORE_DIRS = {'build', 'devel', 'install', 'log', '.git', '__pycache__'}
IGNORED_TOKENS = {'REQUIRED', 'COMPONENTS', 'DEPENDS', 'catkin', 'ament_cmake', 'ament_python', 'system_lib', 'Boost', 'Eigen', 'Eigen3', 'xyz'}


def read_text(path: Path) -> str:
    """! @brief 安全读取文本。"""
    try:
        return path.read_text(encoding='utf-8', errors='ignore')
    except OSError:
        return ''


def strip_comments(cmake_text: str) -> str:
    """! @brief 去掉 CMake 注释，减少误报。"""
    return '\n'.join(line.split('#', 1)[0] for line in cmake_text.splitlines())


def iter_package_xml(root: Path):
    """! @brief 枚举 package.xml。"""
    for path in root.rglob('package.xml'):
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        yield path


def xml_deps(package_xml: Path) -> set[str]:
    """! @brief 从 package.xml 提取依赖名。"""
    deps: set[str] = set()
    tree = ET.parse(package_xml)
    xml_root = tree.getroot()
    for tag in ['depend', 'build_depend', 'build_export_depend', 'exec_depend', 'run_depend', 'test_depend']:
        for node in xml_root.findall(tag):
            if node.text and node.text.strip():
                deps.add(node.text.strip())
    return deps


def detect_build_type(package_xml: Path, cmake_text: str) -> str:
    """! @brief 判断包类型。"""
    xml_text = read_text(package_xml)
    if '<buildtool_depend>catkin</buildtool_depend>' in xml_text or 'find_package(catkin' in cmake_text:
        return 'ros1-catkin'
    if 'ament_package(' in cmake_text or '<buildtool_depend>ament_cmake</buildtool_depend>' in xml_text or '<buildtool_depend>ament_python</buildtool_depend>' in xml_text:
        return 'ros2-colcon'
    return 'unknown'


def cmake_mentions(cmake_text: str) -> set[str]:
    """! @brief 从 CMakeLists.txt 粗略提取依赖。"""
    cleaned = strip_comments(cmake_text)
    deps: set[str] = set()
    match = re.search(r'find_package\(catkin\s+REQUIRED\s+COMPONENTS\s+([^\)]*)\)', cleaned, re.S)
    if match:
        deps.update(re.findall(r'[A-Za-z0-9_\-]+', match.group(1)))
    for match in re.finditer(r'find_package\(([A-Za-z0-9_\-]+)\s+REQUIRED', cleaned):
        deps.add(match.group(1))
    for match in re.finditer(r'ament_target_dependencies\([^\)]*?\s([A-Za-z0-9_\-\s]+)\)', cleaned, re.S):
        deps.update(re.findall(r'[A-Za-z0-9_\-]+', match.group(1)))
    for match in re.finditer(r'catkin_package\([^\)]*CATKIN_DEPENDS\s+([^\)]*)\)', cleaned, re.S):
        deps.update(re.findall(r'[A-Za-z0-9_\-]+', match.group(1)))
    return {item for item in deps if item not in IGNORED_TOKENS}


def ros2_install_warnings(package_dir: Path, cmake_text: str) -> list[str]:
    """! @brief 检查 ROS 2 常见资源目录是否有安装规则。"""
    warnings: list[str] = []
    normalized = '\n'.join(strip_comments(cmake_text).splitlines())
    for dirname in ['launch', 'config', 'urdf', 'rviz']:
        if not (package_dir / dirname).exists():
            continue
        direct_token = f'DIRECTORY {dirname}'
        multiline_token = f'DIRECTORY\n  {dirname}'
        if direct_token not in normalized and multiline_token not in normalized:
            warnings.append(f'存在目录 {dirname}/，但未发现明显的 install(DIRECTORY {dirname} ...) 规则')
    return warnings


def check_workspace(root: Path) -> int:
    """! @brief 扫描工作区并输出告警。"""
    issues = 0
    for package_xml in iter_package_xml(root):
        package_dir = package_xml.parent
        cmake_text = read_text(package_dir / 'CMakeLists.txt')
        if not cmake_text:
            continue
        build_type = detect_build_type(package_xml, cmake_text)
        declared = xml_deps(package_xml)
        mentioned = cmake_mentions(cmake_text)
        missing = sorted(dep for dep in mentioned if dep not in declared)
        print(f'[{package_dir.name}] {build_type}')
        if build_type == 'ros1-catkin' and 'find_package(catkin' not in cmake_text:
            print('  - 告警：package.xml 显示是 catkin 包，但 CMakeLists.txt 中未发现 find_package(catkin ...)')
            issues += 1
        if build_type == 'ros2-colcon' and 'ament_package(' not in cmake_text:
            print('  - 告警：疑似 ROS2 包，但 CMakeLists.txt 中未发现 ament_package()')
            issues += 1
        if missing:
            print(f'  - 告警：CMake 中提到了依赖，但 package.xml 未声明：{", ".join(missing)}')
            issues += 1
        if build_type == 'ros2-colcon':
            for warning in ros2_install_warnings(package_dir, cmake_text):
                print(f'  - 告警：{warning}')
                issues += 1
    return issues


def main() -> None:
    """! @brief CLI 入口。"""
    parser = argparse.ArgumentParser(description='检查 ROS 工作区的一致性')
    parser.add_argument('path', nargs='?', default='.', help='工作区根目录')
    args = parser.parse_args()
    root = Path(args.path).resolve()
    issues = check_workspace(root)
    print(f'\n总告警数: {issues}')


if __name__ == '__main__':
    main()
