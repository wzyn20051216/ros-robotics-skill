#!/usr/bin/env python3
"""! @brief ?? ROS ??????????????????"""

from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path

IGNORE_DIRS = {'build', 'devel', 'install', 'log', '.git', '__pycache__'}


def read_text(path: Path) -> str:
    """! @brief ???????"""
    try:
        return path.read_text(encoding='utf-8', errors='ignore')
    except OSError:
        return ''


def iter_package_xml(root: Path):
    """! @brief ?? package.xml?"""
    for path in root.rglob('package.xml'):
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        yield path


def xml_deps(package_xml: Path) -> set[str]:
    """! @brief ? package.xml ??????"""
    deps: set[str] = set()
    tree = ET.parse(package_xml)
    xml_root = tree.getroot()
    for tag in ['depend', 'build_depend', 'build_export_depend', 'exec_depend', 'run_depend', 'test_depend']:
        for node in xml_root.findall(tag):
            if node.text and node.text.strip():
                deps.add(node.text.strip())
    return deps


def detect_build_type(package_xml: Path, cmake_text: str) -> str:
    """! @brief ??????"""
    xml_text = read_text(package_xml)
    if '<buildtool_depend>catkin</buildtool_depend>' in xml_text or 'find_package(catkin' in cmake_text:
        return 'ros1-catkin'
    if 'ament_package(' in cmake_text or '<buildtool_depend>ament_cmake</buildtool_depend>' in xml_text or '<buildtool_depend>ament_python</buildtool_depend>' in xml_text:
        return 'ros2-colcon'
    return 'unknown'


def cmake_mentions(cmake_text: str) -> set[str]:
    """! @brief ? CMakeLists.txt ???????"""
    deps: set[str] = set()

    match = re.search(r'find_package\(catkin\s+REQUIRED\s+COMPONENTS\s+([^\)]*)\)', cmake_text, re.S)
    if match:
        deps.update(re.findall(r'[A-Za-z0-9_\-]+', match.group(1)))

    for match in re.finditer(r'find_package\(([A-Za-z0-9_\-]+)\s+REQUIRED', cmake_text):
        deps.add(match.group(1))

    for match in re.finditer(r'ament_target_dependencies\([^\)]*?\s([A-Za-z0-9_\-\s]+)\)', cmake_text, re.S):
        deps.update(re.findall(r'[A-Za-z0-9_\-]+', match.group(1)))

    for match in re.finditer(r'catkin_package\([^\)]*CATKIN_DEPENDS\s+([^\)]*)\)', cmake_text, re.S):
        deps.update(re.findall(r'[A-Za-z0-9_\-]+', match.group(1)))

    return {item for item in deps if item not in {'REQUIRED', 'COMPONENTS', 'DEPENDS', 'catkin', 'ament_cmake', 'ament_python', 'system_lib', 'Boost', 'Eigen', 'Eigen3'}}


def ros2_install_warnings(package_dir: Path, cmake_text: str) -> list[str]:
    """! @brief ?? ROS 2 ??????????????"""
    warnings: list[str] = []
    normalized = '\n'.join(cmake_text.splitlines())
    for dirname in ['launch', 'config', 'urdf', 'rviz']:
        if not (package_dir / dirname).exists():
            continue
        direct_token = f'DIRECTORY {dirname}'
        multiline_token = f'DIRECTORY\n  {dirname}'
        if direct_token not in normalized and multiline_token not in normalized:
            warnings.append(f'???? {dirname}/???????? install(DIRECTORY {dirname} ...) ??')
    return warnings


def check_workspace(root: Path) -> int:
    """! @brief ???????????"""
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
            print('  - ???package.xml ??? catkin ??? CMakeLists.txt ???? find_package(catkin ...)')
            issues += 1

        if build_type == 'ros2-colcon' and 'ament_package(' not in cmake_text:
            print('  - ????? ROS2 ??? CMakeLists.txt ???? ament_package()')
            issues += 1

        if missing:
            print(f'  - ???CMake ???????? package.xml ????{", ".join(missing)}')
            issues += 1

        if build_type == 'ros2-colcon':
            for warning in ros2_install_warnings(package_dir, cmake_text):
                print(f'  - ???{warning}')
                issues += 1

    return issues


def main() -> None:
    """! @brief CLI ???"""
    parser = argparse.ArgumentParser(description='?? ROS ???????')
    parser.add_argument('path', nargs='?', default='.', help='??????')
    args = parser.parse_args()

    root = Path(args.path).resolve()
    issues = check_workspace(root)
    print(f'\n????: {issues}')


if __name__ == '__main__':
    main()
