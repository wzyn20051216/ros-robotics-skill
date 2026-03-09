#!/usr/bin/env python3
"""! @brief 检查 ROS 工作区里依赖声明与安装规则的一致性（增强版）。

本脚本对工作区内每个含有 package.xml 的 ROS 包执行多项静态检查，
并以人类可读格式或 JSON 格式输出结果。

检查项目：
    - CMake 依赖 vs package.xml 依赖声明
    - 安装规则完整性（launch/config/urdf/rviz/maps/worlds/models/meshes）
    - target_link_libraries 引用的未 find_package 的库
    - add_executable / add_library 目标的 install(TARGETS ...) 覆盖
    - ament_target_dependencies 引用的包是否在 find_package 中声明
    - package.xml 冗余依赖声明检测
    - package.xml test_depend 检测
    - package.xml format 版本建议
    - launch 文件中引用的包名检查
    - launch 文件中硬编码路径警告
    - YAML 参数文件语法检查
    - Python 包 setup.py / setup.cfg 的 data_files 检查
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# 忽略的目录（构建产物、版本控制）
IGNORE_DIRS = {'build', 'devel', 'install', 'log', '.git', '__pycache__'}

# CMake 解析时忽略的关键字和常见系统库
IGNORED_TOKENS = {
    'REQUIRED',
    'COMPONENTS',
    'DEPENDS',
    'catkin',
    'ament_cmake',
    'ament_python',
    'system_lib',
    'Boost',
    'Eigen',
    'Eigen3',
    'xyz',
}

# 常见 ROS 测试框架，用于 test_depend 检查
COMMON_TEST_FRAMEWORKS = {
    'ament_cmake_gtest',
    'ament_lint_auto',
    'ament_lint_common',
    'ament_cmake_pytest',
    'rostest',
    'gtest',
}

# launch 文件中的硬编码路径模式（绝对路径）
HARDCODED_PATH_PATTERN = re.compile(r'["\'](?:/home/|/opt/ros/|/usr/local/)[\w/\.\-]+["\']')

# 严重级别常量
LEVEL_ERROR = 'ERROR'
LEVEL_WARN = 'WARNING'
LEVEL_INFO = 'INFO'


def read_text(path: Path) -> str:
    """! @brief 安全读取文本文件，失败时返回空串。"""
    try:
        return path.read_text(encoding='utf-8', errors='ignore')
    except OSError:
        return ''


def strip_comments(cmake_text: str) -> str:
    """! @brief 去掉 CMake 注释（# 之后的内容），减少误报。"""
    return '\n'.join(line.split('#', 1)[0] for line in cmake_text.splitlines())


def iter_package_xml(root: Path):
    """! @brief 枚举工作区内所有 package.xml，跳过构建/版本控制目录。"""
    for path in root.rglob('package.xml'):
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        yield path


def xml_deps(package_xml: Path) -> set[str]:
    """! @brief 从 package.xml 提取全部依赖名；解析失败时返回空集合。"""
    deps: set[str] = set()
    try:
        tree = ET.parse(package_xml)
    except ET.ParseError:
        return deps
    xml_root = tree.getroot()
    for tag in [
        'depend',
        'build_depend',
        'build_export_depend',
        'exec_depend',
        'run_depend',
        'test_depend',
    ]:
        for node in xml_root.findall(tag):
            if node.text and node.text.strip():
                deps.add(node.text.strip())
    return deps


def detect_build_type(package_xml: Path, cmake_text: str) -> str:
    """! @brief 判断包构建类型：ros1-catkin / ros2-colcon / unknown。"""
    xml_text = read_text(package_xml)
    if (
        '<buildtool_depend>catkin</buildtool_depend>' in xml_text
        or 'find_package(catkin' in cmake_text
    ):
        return 'ros1-catkin'
    if (
        'ament_package(' in cmake_text
        or '<buildtool_depend>ament_cmake</buildtool_depend>' in xml_text
        or '<buildtool_depend>ament_python</buildtool_depend>' in xml_text
    ):
        return 'ros2-colcon'
    return 'unknown'


def cmake_mentions(cmake_text: str) -> set[str]:
    """! @brief 从 CMakeLists.txt 粗略提取所有依赖引用（find_package + ament_target_dependencies + catkin_package）。"""
    cleaned = strip_comments(cmake_text)
    deps: set[str] = set()

    # catkin COMPONENTS
    match = re.search(
        r'find_package\(catkin\s+REQUIRED\s+COMPONENTS\s+([^\)]*)\)',
        cleaned,
        re.S,
    )
    if match:
        deps.update(re.findall(r'[A-Za-z0-9_\-]+', match.group(1)))

    # 独立的 find_package(XXX REQUIRED ...)
    for m in re.finditer(r'find_package\(([A-Za-z0-9_\-]+)\s+REQUIRED', cleaned):
        deps.add(m.group(1))

    # ament_target_dependencies
    for m in re.finditer(
        r'ament_target_dependencies\([^\)]*?\s([A-Za-z0-9_\-\s]+)\)',
        cleaned,
        re.S,
    ):
        deps.update(re.findall(r'[A-Za-z0-9_\-]+', m.group(1)))

    # catkin_package CATKIN_DEPENDS
    for m in re.finditer(
        r'catkin_package\([^\)]*CATKIN_DEPENDS\s+([^\)]*)\)',
        cleaned,
        re.S,
    ):
        deps.update(re.findall(r'[A-Za-z0-9_\-]+', m.group(1)))

    return {item for item in deps if item not in IGNORED_TOKENS}


def ros2_install_warnings(package_dir: Path, cmake_text: str) -> list[str]:
    """! @brief 检查 ROS 2 常见资源目录是否存在对应安装规则。

    检查范围：launch, config, urdf, rviz, maps, worlds, models, meshes。
    """
    warnings: list[str] = []
    normalized = '\n'.join(strip_comments(cmake_text).splitlines())

    # 扩展检查目录列表（新增 maps/worlds/models/meshes）
    for dirname in ['launch', 'config', 'urdf', 'rviz', 'maps', 'worlds', 'models', 'meshes']:
        if not (package_dir / dirname).exists():
            continue
        direct_token = f'DIRECTORY {dirname}'
        multiline_token = f'DIRECTORY\n  {dirname}'
        if direct_token not in normalized and multiline_token not in normalized:
            warnings.append(
                f'存在目录 {dirname}/，但未发现明显的 install(DIRECTORY {dirname} ...) 规则'
            )
    return warnings


# ---------------------------------------------------------------------------
# 新增检查：CMakeLists.txt 深度分析
# ---------------------------------------------------------------------------


def _extract_find_package_names(cmake_text: str) -> set[str]:
    """! @brief 提取所有 find_package(...) 中声明的包名（不含关键字）。"""
    cleaned = strip_comments(cmake_text)
    found: set[str] = set()

    # find_package(XXX ...) 形式
    for m in re.finditer(r'find_package\(\s*([A-Za-z0-9_\-]+)', cleaned):
        pkg = m.group(1)
        if pkg not in IGNORED_TOKENS:
            found.add(pkg)

    # catkin COMPONENTS 中的子包
    m = re.search(
        r'find_package\(catkin\s+REQUIRED\s+COMPONENTS\s+([^\)]*)\)',
        cleaned,
        re.S,
    )
    if m:
        for name in re.findall(r'[A-Za-z0-9_\-]+', m.group(1)):
            if name not in IGNORED_TOKENS:
                found.add(name)

    return found


def check_target_link_libraries(cmake_text: str) -> list[tuple[str, str]]:
    """! @brief 检查 target_link_libraries 中引用但未 find_package 的库。

    返回 list[(level, message)] 形式。
    """
    results: list[tuple[str, str]] = []
    cleaned = strip_comments(cmake_text)
    found_pkgs = _extract_find_package_names(cmake_text)

    # 提取所有 target_link_libraries(target lib1 lib2 ...) 中的库名
    tll_libs: set[str] = set()
    for m in re.finditer(r'target_link_libraries\(\s*\S+\s+([^\)]+)\)', cleaned, re.S):
        raw = m.group(1)
        for token in re.findall(r'[A-Za-z0-9_:\-]+', raw):
            # 过滤 cmake 关键字和已知系统符号
            if token in {'PUBLIC', 'PRIVATE', 'INTERFACE'} or token in IGNORED_TOKENS:
                continue
            # 带命名空间的 :: 形式（如 rclcpp::rclcpp），取命名空间前缀
            if '::' in token:
                tll_libs.add(token.split('::')[0])
            else:
                tll_libs.add(token)

    # 比对：tll_libs 中不在 find_package 结果内的
    for lib in sorted(tll_libs):
        if lib and lib not in found_pkgs:
            results.append((
                LEVEL_WARN,
                f'target_link_libraries 引用了 "{lib}"，但未在 find_package 中查找',
            ))
    return results


def check_install_targets(cmake_text: str) -> list[tuple[str, str]]:
    """! @brief 检查 add_executable / add_library 目标是否有对应 install(TARGETS ...) 规则。

    返回 list[(level, message)] 形式。
    """
    results: list[tuple[str, str]] = []
    cleaned = strip_comments(cmake_text)

    # 提取 add_executable(target_name ...) 和 add_library(target_name ...) 中的目标名
    defined_targets: set[str] = set()
    for m in re.finditer(r'(?:add_executable|add_library)\(\s*([A-Za-z0-9_\-]+)', cleaned):
        defined_targets.add(m.group(1))

    if not defined_targets:
        return results

    # 提取 install(TARGETS ...) 中列出的目标名
    installed_targets: set[str] = set()
    for m in re.finditer(r'install\(\s*TARGETS\s+([^\)]+)\)', cleaned, re.S):
        raw = m.group(1)
        for token in re.findall(r'[A-Za-z0-9_\-]+', raw):
            # 过滤 install 关键字
            if token not in {
                'RUNTIME',
                'LIBRARY',
                'ARCHIVE',
                'DESTINATION',
                'COMPONENT',
                'OPTIONAL',
                'NAMELINK_ONLY',
                'NAMELINK_SKIP',
            }:
                installed_targets.add(token)

    # 找出缺少安装规则的目标
    for target in sorted(defined_targets):
        if target not in installed_targets:
            results.append((
                LEVEL_WARN,
                f'目标 "{target}" 已定义（add_executable/add_library），但未找到 install(TARGETS {target} ...) 规则',
            ))
    return results


def check_ament_target_deps_vs_find_package(cmake_text: str) -> list[tuple[str, str]]:
    """! @brief 检查 ament_target_dependencies 引用的包是否在 find_package 中声明。

    返回 list[(level, message)] 形式。
    """
    results: list[tuple[str, str]] = []
    cleaned = strip_comments(cmake_text)
    found_pkgs = _extract_find_package_names(cmake_text)

    for m in re.finditer(
        r'ament_target_dependencies\(\s*\S+\s+([^\)]+)\)',
        cleaned,
        re.S,
    ):
        raw = m.group(1)
        for dep in re.findall(r'[A-Za-z0-9_\-]+', raw):
            if dep in IGNORED_TOKENS:
                continue
            if dep not in found_pkgs:
                results.append((
                    LEVEL_WARN,
                    f'ament_target_dependencies 引用了 "{dep}"，但未在 find_package 中声明',
                ))
    return results


# ---------------------------------------------------------------------------
# 新增检查：package.xml 深度分析
# ---------------------------------------------------------------------------


def check_package_xml_redundant_deps(package_xml: Path) -> list[tuple[str, str]]:
    """! @brief 检查 <depend> 与 <build_depend> + <exec_depend> 的冗余声明。

    返回 list[(level, message)] 形式。
    """
    results: list[tuple[str, str]] = []
    try:
        tree = ET.parse(package_xml)
    except ET.ParseError:
        return results

    xml_root = tree.getroot()

    # 收集各类依赖集合
    depend_set: set[str] = set()
    build_set: set[str] = set()
    exec_set: set[str] = set()

    for node in xml_root.findall('depend'):
        if node.text and node.text.strip():
            depend_set.add(node.text.strip())
    for node in xml_root.findall('build_depend'):
        if node.text and node.text.strip():
            build_set.add(node.text.strip())
    for node in xml_root.findall('exec_depend'):
        if node.text and node.text.strip():
            exec_set.add(node.text.strip())

    # <depend> 等价于同时声明 build+exec；若三者同时出现则冗余
    for dep in sorted(depend_set):
        if dep in build_set and dep in exec_set:
            results.append((
                LEVEL_INFO,
                f'"{dep}" 同时出现在 <depend>、<build_depend> 和 <exec_depend> 中，存在冗余声明',
            ))
        elif dep in build_set:
            results.append((
                LEVEL_INFO,
                f'"{dep}" 同时出现在 <depend> 和 <build_depend> 中，<build_depend> 可省略',
            ))
        elif dep in exec_set:
            results.append((
                LEVEL_INFO,
                f'"{dep}" 同时出现在 <depend> 和 <exec_depend> 中，<exec_depend> 可省略',
            ))
    return results


def check_package_xml_test_deps(package_xml: Path) -> list[tuple[str, str]]:
    """! @brief 检查 <test_depend> 是否包含常见测试框架。

    返回 list[(level, message)] 形式。
    """
    results: list[tuple[str, str]] = []
    try:
        tree = ET.parse(package_xml)
    except ET.ParseError:
        return results

    xml_root = tree.getroot()
    test_deps: set[str] = set()
    for node in xml_root.findall('test_depend'):
        if node.text and node.text.strip():
            test_deps.add(node.text.strip())

    # 如果有 test_depend 节点但不包含任何常见测试框架
    if test_deps and not (test_deps & COMMON_TEST_FRAMEWORKS):
        results.append((
            LEVEL_INFO,
            f'<test_depend> 中未发现常见测试框架（{", ".join(sorted(COMMON_TEST_FRAMEWORKS))}），请确认测试依赖完整',
        ))
    return results


def check_package_xml_format(package_xml: Path) -> list[tuple[str, str]]:
    """! @brief 检查 package.xml 的 format 版本，建议使用 format="3"。

    返回 list[(level, message)] 形式。
    """
    results: list[tuple[str, str]] = []
    try:
        tree = ET.parse(package_xml)
    except ET.ParseError:
        results.append((LEVEL_ERROR, 'package.xml 解析失败，XML 格式有误'))
        return results

    xml_root = tree.getroot()
    fmt = xml_root.get('format')
    if fmt is None:
        results.append((
            LEVEL_INFO,
            'package.xml 未声明 format 属性，建议添加 format="3"',
        ))
    elif fmt != '3':
        results.append((
            LEVEL_INFO,
            f'package.xml 使用 format="{fmt}"，建议升级到 format="3"',
        ))
    return results


# ---------------------------------------------------------------------------
# 新增检查：launch 文件分析
# ---------------------------------------------------------------------------


def _get_launch_pkg_refs_python(launch_text: str) -> set[str]:
    """! @brief 从 Python launch 文件中提取引用的包名。"""
    pkgs: set[str] = set()

    # get_package_share_directory('pkg_name') 模式
    for m in re.finditer(r'get_package_share_directory\(["\']([^"\']+)["\']\)', launch_text):
        pkgs.add(m.group(1))

    # FindPackageShare('pkg_name') 模式
    for m in re.finditer(r'FindPackageShare\(["\']([^"\']+)["\']\)', launch_text):
        pkgs.add(m.group(1))

    # Node(package='pkg_name') 模式
    for m in re.finditer(r'package\s*=\s*["\']([^"\']+)["\']', launch_text):
        pkgs.add(m.group(1))

    return pkgs


def _get_launch_pkg_refs_xml(launch_text: str) -> set[str]:
    """! @brief 从 XML launch 文件中提取引用的包名。"""
    pkgs: set[str] = set()
    try:
        xml_root = ET.fromstring(launch_text)
    except ET.ParseError:
        return pkgs

    # <node pkg="..."> 和 <include file="$(find pkg_name)/...">
    for node in xml_root.iter():
        pkg_attr = node.get('pkg')
        if pkg_attr:
            pkgs.add(pkg_attr)
        file_attr = node.get('file') or ''
        for m in re.finditer(r'\$\(find\s+([A-Za-z0-9_\-]+)\)', file_attr):
            pkgs.add(m.group(1))
    return pkgs


def check_launch_files(package_dir: Path, declared_deps: set[str]) -> list[tuple[str, str]]:
    """! @brief 扫描 launch/*.py 和 launch/*.xml，检查引用包是否在 package.xml 中声明。

    同时检查 launch 文件中的硬编码绝对路径。
    返回 list[(level, message)] 形式。
    """
    results: list[tuple[str, str]] = []
    launch_dir = package_dir / 'launch'
    if not launch_dir.exists():
        return results

    for launch_file in launch_dir.iterdir():
        if not launch_file.is_file():
            continue

        launch_text = read_text(launch_file)
        if not launch_text:
            continue

        # 检查硬编码路径
        hardcoded = HARDCODED_PATH_PATTERN.findall(launch_text)
        for path_str in hardcoded:
            results.append((
                LEVEL_WARN,
                f'launch/{launch_file.name} 中存在硬编码路径：{path_str}',
            ))

        # 提取包引用
        if launch_file.suffix == '.py':
            pkg_refs = _get_launch_pkg_refs_python(launch_text)
        elif launch_file.suffix == '.xml':
            pkg_refs = _get_launch_pkg_refs_xml(launch_text)
        else:
            continue

        # 获取当前包名
        package_xml = package_dir / 'package.xml'
        current_pkg_name = _get_package_name(package_xml)

        for pkg in sorted(pkg_refs):
            # 跳过自身引用
            if pkg == current_pkg_name:
                continue
            if pkg not in declared_deps:
                results.append((
                    LEVEL_WARN,
                    f'launch/{launch_file.name} 中引用了包 "{pkg}"，但未在 package.xml 中声明',
                ))
    return results


def _get_package_name(package_xml: Path) -> str:
    """! @brief 从 package.xml 提取包名，失败时返回空串。"""
    try:
        tree = ET.parse(package_xml)
    except ET.ParseError:
        return ''
    name_node = tree.getroot().find('name')
    if name_node is not None and name_node.text:
        return name_node.text.strip()
    return ''


# ---------------------------------------------------------------------------
# 新增检查：YAML 参数文件语法检查
# ---------------------------------------------------------------------------


def _basic_yaml_check(yaml_text: str) -> list[str]:
    """! @brief 对 YAML 文本进行基础格式检查（不依赖 PyYAML）。

    仅检查最常见的格式错误：tab 缩进、不平衡引号（单行层面）。
    """
    errors: list[str] = []
    for lineno, line in enumerate(yaml_text.splitlines(), start=1):
        # YAML 禁止使用 tab 作为缩进
        if line.startswith('\t'):
            errors.append(f'第 {lineno} 行：YAML 不允许使用 Tab 缩进')
            continue

        # 检查不平衡的双引号（简单启发式，只检查奇数个双引号）
        stripped = line.split('#', 1)[0]  # 去掉注释部分
        dq_count = stripped.count('"') - stripped.count('\\"')
        if dq_count % 2 != 0:
            errors.append(f'第 {lineno} 行：疑似双引号不平衡')
    return errors


def _try_yaml_with_stdlib(yaml_text: str) -> list[str]:
    """! @brief 尝试用 PyYAML 解析 YAML；若无 PyYAML 则退回基础检查。"""
    try:
        import yaml  # type: ignore[import-untyped]

        try:
            yaml.safe_load(yaml_text)
            return []
        except yaml.YAMLError as exc:
            return [f'YAML 解析错误：{exc}']
    except ImportError:
        # 无 PyYAML，退回基础检查
        return _basic_yaml_check(yaml_text)


def check_yaml_files(package_dir: Path) -> list[tuple[str, str]]:
    """! @brief 检查 config/ 目录下的 YAML 文件是否能正常解析。

    返回 list[(level, message)] 形式。
    """
    results: list[tuple[str, str]] = []
    config_dir = package_dir / 'config'
    if not config_dir.exists():
        return results

    for yaml_file in config_dir.rglob('*'):
        if yaml_file.suffix not in {'.yaml', '.yml'} or not yaml_file.is_file():
            continue
        yaml_text = read_text(yaml_file)
        if not yaml_text:
            continue

        rel = yaml_file.relative_to(package_dir)
        errors = _try_yaml_with_stdlib(yaml_text)
        for err in errors:
            results.append((LEVEL_ERROR, f'{rel}：{err}'))
    return results


# ---------------------------------------------------------------------------
# 新增检查：Python 包 setup.py / setup.cfg data_files 检查
# ---------------------------------------------------------------------------


def check_python_package_data(package_dir: Path) -> list[tuple[str, str]]:
    """! @brief 检查 Python 包 setup.py / setup.cfg 是否包含 data_files 或 package_data。

    返回 list[(level, message)] 形式。
    """
    results: list[tuple[str, str]] = []

    # 只对含 setup.py 的包检查（ament_python 风格）
    setup_py = package_dir / 'setup.py'
    setup_cfg = package_dir / 'setup.cfg'

    if not setup_py.exists() and not setup_cfg.exists():
        return results

    # 检查 setup.py
    if setup_py.exists():
        text = read_text(setup_py)
        has_data = 'data_files' in text or 'package_data' in text
        if not has_data:
            results.append((
                LEVEL_WARN,
                'setup.py 中未发现 data_files 或 package_data，launch/config 等资源可能未被安装',
            ))

    # 检查 setup.cfg（补充，如果存在则也确认）
    if setup_cfg.exists():
        text = read_text(setup_cfg)
        if 'data_files' in text or 'package_data' in text:
            # setup.cfg 中已经有声明，覆盖 setup.py 的警告
            # 移除上面可能已经添加的警告
            results = [(lvl, msg) for lvl, msg in results if 'setup.py' not in msg or 'data_files' not in msg]

    return results


# ---------------------------------------------------------------------------
# 核心检查函数（向后兼容）
# ---------------------------------------------------------------------------


def check_workspace(root: Path) -> int:
    """! @brief 扫描工作区并输出告警；返回 issues 总数（向后兼容）。

    此函数签名与原版保持完全一致：接受 root: Path，返回 int。
    输出格式保持人类可读，每条告警以 '  - 告警：' 前缀开头。
    """
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

        # ------- 原有检查 -------
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


# ---------------------------------------------------------------------------
# 增强检查函数（返回结构化数据）
# ---------------------------------------------------------------------------


def check_workspace_enhanced(root: Path) -> dict:
    """! @brief 扫描工作区，执行全部增强检查，返回结构化结果字典。

    返回格式：
    {
        "workspace": str,
        "packages": [
            {
                "name": str,
                "path": str,
                "build_type": str,
                "issues": [{"level": str, "message": str}, ...]
            },
            ...
        ],
        "summary": {"errors": int, "warnings": int, "info": int}
    }
    """
    result: dict = {
        'workspace': str(root),
        'packages': [],
        'summary': {'errors': 0, 'warnings': 0, 'info': 0},
    }

    for package_xml in iter_package_xml(root):
        package_dir = package_xml.parent
        cmake_text = read_text(package_dir / 'CMakeLists.txt')
        build_type = detect_build_type(package_xml, cmake_text)
        declared = xml_deps(package_xml)
        pkg_name = _get_package_name(package_xml) or package_dir.name

        pkg_issues: list[dict] = []

        def _add(level: str, msg: str) -> None:
            pkg_issues.append({'level': level, 'message': msg})

        # ------- 原有检查（映射到结构化级别）-------
        if cmake_text:
            mentioned = cmake_mentions(cmake_text)
            missing = sorted(dep for dep in mentioned if dep not in declared)

            if build_type == 'ros1-catkin' and 'find_package(catkin' not in cmake_text:
                _add(LEVEL_ERROR, 'package.xml 显示是 catkin 包，但 CMakeLists.txt 中未发现 find_package(catkin ...)')

            if build_type == 'ros2-colcon' and 'ament_package(' not in cmake_text:
                _add(LEVEL_WARN, '疑似 ROS2 包，但 CMakeLists.txt 中未发现 ament_package()')

            if missing:
                _add(LEVEL_WARN, f'CMake 中提到了依赖，但 package.xml 未声明：{", ".join(missing)}')

            if build_type == 'ros2-colcon':
                for w in ros2_install_warnings(package_dir, cmake_text):
                    _add(LEVEL_WARN, w)

            # ------- CMakeLists.txt 深度分析 -------
            for level, msg in check_target_link_libraries(cmake_text):
                _add(level, msg)
            for level, msg in check_install_targets(cmake_text):
                _add(level, msg)
            for level, msg in check_ament_target_deps_vs_find_package(cmake_text):
                _add(level, msg)

        # ------- package.xml 深度分析 -------
        for level, msg in check_package_xml_redundant_deps(package_xml):
            _add(level, msg)
        for level, msg in check_package_xml_test_deps(package_xml):
            _add(level, msg)
        for level, msg in check_package_xml_format(package_xml):
            _add(level, msg)

        # ------- launch 文件检查 -------
        for level, msg in check_launch_files(package_dir, declared):
            _add(level, msg)

        # ------- YAML 文件检查 -------
        for level, msg in check_yaml_files(package_dir):
            _add(level, msg)

        # ------- Python 包 data_files 检查 -------
        for level, msg in check_python_package_data(package_dir):
            _add(level, msg)

        # 汇总统计
        for issue in pkg_issues:
            lvl = issue['level']
            if lvl == LEVEL_ERROR:
                result['summary']['errors'] += 1
            elif lvl == LEVEL_WARN:
                result['summary']['warnings'] += 1
            else:
                result['summary']['info'] += 1

        result['packages'].append({
            'name': pkg_name,
            'path': str(package_dir),
            'build_type': build_type,
            'issues': pkg_issues,
        })

    return result


def print_enhanced_human_readable(result: dict) -> None:
    """! @brief 以人类可读格式输出增强检查结果，标注严重级别。"""
    for pkg in result['packages']:
        print(f'[{pkg["name"]}] {pkg["build_type"]}')
        if not pkg['issues']:
            print('  (无问题)')
            continue
        for issue in pkg['issues']:
            level = issue['level']
            msg = issue['message']
            print(f'  [{level}] {msg}')

    summary = result['summary']
    print(
        f'\n汇总：{summary["errors"]} errors, '
        f'{summary["warnings"]} warnings, '
        f'{summary["info"]} info'
    )


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------


def main() -> None:
    """! @brief CLI 入口，支持 --json 标志输出结构化数据。"""
    parser = argparse.ArgumentParser(description='检查 ROS 工作区的一致性')
    parser.add_argument('path', nargs='?', default='.', help='工作区根目录')
    parser.add_argument('--json', action='store_true', help='以 JSON 格式输出完整检查结果')
    args = parser.parse_args()
    root = Path(args.path).resolve()

    if args.json:
        # JSON 模式：输出完整结构化数据
        result = check_workspace_enhanced(root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        # 以 errors 数量作为退出码
        sys.exit(result['summary']['errors'])
    else:
        # 人类可读模式：先输出增强结果，与原版格式兼容
        result = check_workspace_enhanced(root)
        print_enhanced_human_readable(result)


if __name__ == '__main__':
    main()
