#!/usr/bin/env python3
"""! @brief 离线解析 URDF/Xacro 文件，检查 TF 树的完整性。

支持功能：
- 解析 URDF XML（如果系统安装了 xacro 命令，也可先展开 xacro）
- 提取所有 link/joint，构建父子有向图
- 检查单根性、悬挂 link、重复名称、循环依赖
- 以树形结构打印 TF 树
- 支持 --json 以 JSON 格式输出结果
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------

@dataclass
class JointInfo:
    """! @brief 单个关节的信息。"""
    name: str
    joint_type: str   # fixed / revolute / continuous / prismatic / planar / floating
    parent: str       # 父 link 名称
    child: str        # 子 link 名称


@dataclass
class TFCheckResult:
    """! @brief TF 树检查的汇总结果。"""
    file: str
    link_count: int
    joint_count: int
    root_links: list[str]
    links: list[str]
    joints: list[JointInfo]
    # 检查项结果
    duplicate_link_names: list[str] = field(default_factory=list)
    duplicate_joint_names: list[str] = field(default_factory=list)
    dangling_links: list[str] = field(default_factory=list)
    circular_dependencies: list[list[str]] = field(default_factory=list)
    warnings: int = 0
    errors: int = 0
    # 树形结构（纯文本行列表，供 JSON 也可保存）
    tree_lines: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# URDF 解析
# ---------------------------------------------------------------------------

def _try_expand_xacro(urdf_path: str) -> Optional[str]:
    """! @brief 尝试用系统 xacro 命令展开文件，返回展开后的 XML 字符串；失败则返回 None。"""
    try:
        result = subprocess.run(
            ['xacro', urdf_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
        # xacro 命令存在但出错，打印警告后继续用原文件
        print(f'  [警告] xacro 展开失败，将直接解析原始文件：{result.stderr.strip()[:200]}',
              file=sys.stderr)
        return None
    except FileNotFoundError:
        # xacro 命令不在 PATH 中，静默忽略，直接解析原始 XML
        return None
    except subprocess.TimeoutExpired:
        print('  [警告] xacro 展开超时，将直接解析原始文件', file=sys.stderr)
        return None


def parse_urdf(urdf_path: str) -> tuple[list[str], list[JointInfo]]:
    """! @brief 解析 URDF 文件，返回 (links 列表, joints 列表)。

    如果文件扩展名含有 "xacro"，且系统有 xacro 命令，会先展开再解析。
    解析失败时抛出 ValueError。
    """
    # 如果是 xacro 文件，尝试展开
    xml_source: Optional[str] = None
    _, ext = os.path.splitext(urdf_path)
    if 'xacro' in ext.lower():
        xml_source = _try_expand_xacro(urdf_path)

    try:
        if xml_source is not None:
            root = ET.fromstring(xml_source)
        else:
            tree = ET.parse(urdf_path)
            root = tree.getroot()
    except ET.ParseError as exc:
        raise ValueError(f'XML 解析失败: {exc}') from exc

    # 提取所有 <link name="..."/>
    links: list[str] = []
    for elem in root.iter('link'):
        name = elem.get('name', '').strip()
        if name:
            links.append(name)

    # 提取所有 <joint name="..." type="...">
    joints: list[JointInfo] = []
    for elem in root.iter('joint'):
        j_name = elem.get('name', '').strip()
        j_type = elem.get('type', 'unknown').strip()
        parent_elem = elem.find('parent')
        child_elem = elem.find('child')
        if parent_elem is None or child_elem is None:
            continue
        parent_link = parent_elem.get('link', '').strip()
        child_link = child_elem.get('link', '').strip()
        if j_name and parent_link and child_link:
            joints.append(JointInfo(
                name=j_name,
                joint_type=j_type,
                parent=parent_link,
                child=child_link,
            ))

    return links, joints


# ---------------------------------------------------------------------------
# TF 树完整性检查
# ---------------------------------------------------------------------------

def find_duplicates(names: list[str]) -> list[str]:
    """! @brief 找出列表中重复出现的名称。"""
    seen: set[str] = set()
    duplicates: list[str] = []
    for name in names:
        if name in seen and name not in duplicates:
            duplicates.append(name)
        seen.add(name)
    return sorted(duplicates)


def find_root_links(links: list[str], joints: list[JointInfo]) -> list[str]:
    """! @brief 找出没有任何关节以其为 child 的 link（即根链接）。"""
    # 所有被某个关节作为 child 的 link
    child_set: set[str] = {j.child for j in joints}
    return [lk for lk in links if lk not in child_set]


def find_dangling_links(links: list[str], joints: list[JointInfo]) -> list[str]:
    """! @brief 找出既不是任何关节的 parent 也不是任何关节的 child 的悬挂 link。

    根链接（root link）不算悬挂，只要其至少是某个关节的 parent 即可。
    完全孤立（既无 parent 关系也无 child 关系）的 link 才视为悬挂。
    """
    connected: set[str] = set()
    for j in joints:
        connected.add(j.parent)
        connected.add(j.child)
    return [lk for lk in links if lk not in connected]


def detect_cycles(
    links: list[str],
    joints: list[JointInfo],
) -> list[list[str]]:
    """! @brief 使用深度优先搜索（DFS）检测有向图中的循环依赖。

    返回包含循环路径的列表（每个元素是一条环路上的节点列表）。
    """
    # 构建邻接表：parent -> [children]
    adj: dict[str, list[str]] = {lk: [] for lk in links}
    for j in joints:
        if j.parent in adj:
            adj[j.parent].append(j.child)
        else:
            adj[j.parent] = [j.child]

    # DFS 颜色标记：0=未访问，1=访问中（在栈上），2=已完成
    color: dict[str, int] = {lk: 0 for lk in links}
    stack: list[str] = []
    cycles: list[list[str]] = []

    def dfs(node: str) -> None:
        color[node] = 1
        stack.append(node)
        for neighbor in adj.get(node, []):
            if color.get(neighbor, 0) == 0:
                dfs(neighbor)
            elif color.get(neighbor, 0) == 1:
                # 找到环：从 neighbor 在 stack 中的位置截取
                cycle_start = stack.index(neighbor)
                cycles.append(stack[cycle_start:] + [neighbor])
        stack.pop()
        color[node] = 2

    for lk in links:
        if color.get(lk, 0) == 0:
            dfs(lk)

    return cycles


# ---------------------------------------------------------------------------
# 树形打印
# ---------------------------------------------------------------------------

def _build_tree_lines(
    node: str,
    children_map: dict[str, list[tuple[str, str]]],  # link -> [(child_link, joint_type)]
    prefix: str = '',
    is_last: bool = True,
) -> list[str]:
    """! @brief 递归地将子树渲染为带 ASCII 分支符号的文本行列表。"""
    connector = '└── ' if is_last else '├── '
    lines = [prefix + connector + node]
    child_prefix = prefix + ('    ' if is_last else '│   ')
    children = children_map.get(node, [])
    for i, (child, jtype) in enumerate(children):
        child_is_last = (i == len(children) - 1)
        sub_lines = _build_tree_lines(child, children_map, child_prefix, child_is_last)
        # 修正第一行（已由递归生成，格式已正确）
        lines.extend(sub_lines)
    return lines


def build_tree_text(
    root_links: list[str],
    joints: list[JointInfo],
) -> list[str]:
    """! @brief 从根链接出发，生成整棵 TF 树的文本行列表。"""
    # 构建 children_map：parent -> [(child, joint_type)]
    children_map: dict[str, list[tuple[str, str]]] = {}
    for j in joints:
        children_map.setdefault(j.parent, []).append((j.child, j.joint_type))

    lines: list[str] = []
    for root_lk in root_links:
        # 根节点本身不需要 connector 前缀
        lines.append(root_lk)
        children = children_map.get(root_lk, [])
        for i, (child, jtype) in enumerate(children):
            is_last = (i == len(children) - 1)
            child_lines = _build_tree_lines(child, children_map, prefix='', is_last=is_last)
            # 第一行追加关节类型标注
            if child_lines:
                child_lines[0] = child_lines[0].rstrip()
                # 已经包含 child 名称，追加 (jtype)
                # 格式：└── child_name (jtype)
                # _build_tree_lines 在第一行只含 child（不含 jtype），在这里补加
                # 但实际上 _build_tree_lines 的第一行就是 prefix+connector+node
                # node 传的是 child（不含 jtype），所以在此追加
                child_lines[0] = child_lines[0] + f' ({jtype})'
            lines.extend(child_lines)
    return lines


def _build_children_map(
    joints: list[JointInfo],
) -> dict[str, list[tuple[str, str]]]:
    """! @brief 构建父 link -> [(子 link, 关节类型)] 的映射表。"""
    result: dict[str, list[tuple[str, str]]] = {}
    for j in joints:
        result.setdefault(j.parent, []).append((j.child, j.joint_type))
    return result


def render_tree(root_links: list[str], joints: list[JointInfo]) -> list[str]:
    """! @brief 生成最终树形文本行（支持多根节点）。

    采用标准 ASCII 树形符号: ├──, └──, │。
    关节类型附在子节点名称后的括号中。
    """
    children_map = _build_children_map(joints)
    lines: list[str] = []

    def _render(node: str, prefix: str, connector: str) -> None:
        lines.append(prefix + connector + node)
        child_prefix = prefix + ('    ' if connector in ('└── ', '') else '│   ')
        children = children_map.get(node, [])
        for i, (child, jtype) in enumerate(children):
            is_last_child = (i == len(children) - 1)
            child_connector = '└── ' if is_last_child else '├── '
            # 把关节类型嵌入子节点显示名
            display = f'{child} ({jtype})'
            # 我们需要 display 作为 node 但已含括号；直接追加文本
            # 为保持递归结构统一，将 display 作为 node 传入
            _render(display, child_prefix, child_connector)

    for root_lk in root_links:
        # 根节点无需 connector
        _render(root_lk, prefix='', connector='')

    # 过滤掉第一行开头空字符串产生的前导空格
    return [ln.lstrip('') for ln in lines]


# ---------------------------------------------------------------------------
# 核心检查流程
# ---------------------------------------------------------------------------

def check_tf_tree(urdf_path: str) -> TFCheckResult:
    """! @brief 对给定的 URDF/Xacro 文件执行完整的 TF 树检查。

    Args:
        urdf_path: URDF 或 Xacro 文件的路径（绝对或相对均可）。

    Returns:
        TFCheckResult 数据类，包含所有检查项的结果。

    Raises:
        FileNotFoundError: 文件不存在。
        ValueError: XML 解析失败。
    """
    abs_path = os.path.abspath(urdf_path)
    if not os.path.isfile(abs_path):
        raise FileNotFoundError(f'文件不存在: {abs_path}')

    links, joints = parse_urdf(abs_path)

    result = TFCheckResult(
        file=abs_path,
        link_count=len(links),
        joint_count=len(joints),
        root_links=[],
        links=links,
        joints=joints,
    )

    # 1. 重复名称检查
    result.duplicate_link_names = find_duplicates([lk for lk in links])
    result.duplicate_joint_names = find_duplicates([j.name for j in joints])

    # 2. 单根性检查（需要先去重，用 set 做有效 link 集合）
    result.root_links = find_root_links(links, joints)

    # 3. 悬挂 link 检查
    result.dangling_links = find_dangling_links(links, joints)

    # 4. 循环依赖检查
    result.circular_dependencies = detect_cycles(links, joints)

    # 5. 生成树形文本
    result.tree_lines = render_tree(result.root_links, joints)

    # 6. 统计警告/错误数
    warnings = 0
    errors = 0

    # 重复名称 -> 错误
    if result.duplicate_link_names:
        errors += len(result.duplicate_link_names)
    if result.duplicate_joint_names:
        errors += len(result.duplicate_joint_names)

    # 多根或无根 -> 错误
    if len(result.root_links) != 1:
        errors += 1

    # 悬挂 link -> 警告
    warnings += len(result.dangling_links)

    # 循环依赖 -> 错误
    errors += len(result.circular_dependencies)

    result.warnings = warnings
    result.errors = errors

    return result


# ---------------------------------------------------------------------------
# 输出格式化
# ---------------------------------------------------------------------------

def _status_mark(ok: bool) -> str:
    """! @brief 返回通过/失败的文本标记（避免 emoji 在部分终端乱码，使用 ASCII）。"""
    return '[OK]' if ok else '[!!]'


def print_human_readable(result: TFCheckResult) -> None:
    """! @brief 以人类可读格式打印 TF 树检查结果。"""
    sep = '=' * 40
    print(sep)
    print('=== TF 树完整性检查 ===')
    print(sep)
    print(f'文件      : {result.file}')
    print(f'链接数    : {result.link_count}')
    print(f'关节数    : {result.joint_count}')

    if result.root_links:
        print(f'根链接    : {", ".join(result.root_links)}')
    else:
        print('根链接    : （未找到）')

    # 打印树形结构
    if result.tree_lines:
        print()
        print('TF 树结构:')
        for line in result.tree_lines:
            print(line)
    else:
        print()
        print('TF 树结构: （无法构建，请检查链接/关节定义）')

    print()
    print('--- 检查项 ---')

    # 单根性检查
    root_count = len(result.root_links)
    if root_count == 1:
        print(f'{_status_mark(True)} TF 树单根性检查通过（根链接: {result.root_links[0]}）')
    elif root_count == 0:
        print(f'{_status_mark(False)} TF 树无根节点（所有 link 都被某个 joint 作为 child）')
    else:
        roots_str = ', '.join(result.root_links)
        print(f'{_status_mark(False)} TF 树存在多个根节点（{root_count} 个）: {roots_str}')

    # 悬挂 link
    if not result.dangling_links:
        print(f'{_status_mark(True)} 无悬挂链接')
    else:
        dangling_str = ', '.join(result.dangling_links)
        print(f'{_status_mark(False)} 发现 {len(result.dangling_links)} 个悬挂链接: {dangling_str}')

    # 重复名称
    dup_ok = not result.duplicate_link_names and not result.duplicate_joint_names
    if dup_ok:
        print(f'{_status_mark(True)} 无重复名称')
    else:
        if result.duplicate_link_names:
            print(f'{_status_mark(False)} 重复 link 名称: {", ".join(result.duplicate_link_names)}')
        if result.duplicate_joint_names:
            print(f'{_status_mark(False)} 重复 joint 名称: {", ".join(result.duplicate_joint_names)}')

    # 循环依赖
    if not result.circular_dependencies:
        print(f'{_status_mark(True)} 无循环依赖')
    else:
        print(f'{_status_mark(False)} 发现 {len(result.circular_dependencies)} 条循环依赖:')
        for cycle in result.circular_dependencies:
            print(f'    {"->".join(cycle)}')

    print()
    print(f'总计: {result.warnings} 个警告, {result.errors} 个错误')


def result_to_dict(result: TFCheckResult) -> dict:
    """! @brief 将 TFCheckResult 转换为可 JSON 序列化的字典。"""
    return {
        'file': result.file,
        'link_count': result.link_count,
        'joint_count': result.joint_count,
        'root_links': result.root_links,
        'links': result.links,
        'joints': [
            {
                'name': j.name,
                'type': j.joint_type,
                'parent': j.parent,
                'child': j.child,
            }
            for j in result.joints
        ],
        'duplicate_link_names': result.duplicate_link_names,
        'duplicate_joint_names': result.duplicate_joint_names,
        'dangling_links': result.dangling_links,
        'circular_dependencies': result.circular_dependencies,
        'tree_lines': result.tree_lines,
        'warnings': result.warnings,
        'errors': result.errors,
    }


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main() -> None:
    """! @brief CLI 入口：解析参数，执行检查，输出结果。"""
    parser = argparse.ArgumentParser(
        description='离线检查 URDF/Xacro 文件的 TF 树完整性',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            '示例:\n'
            '  python check_tf_tree.py robot.urdf\n'
            '  python check_tf_tree.py robot.urdf.xacro\n'
            '  python check_tf_tree.py robot.urdf --json\n'
        ),
    )
    parser.add_argument(
        'urdf_file',
        help='URDF 或 Xacro 文件路径',
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='以 JSON 格式输出检查结果',
    )
    args = parser.parse_args()

    try:
        result = check_tf_tree(args.urdf_file)
    except FileNotFoundError as exc:
        print(f'[错误] {exc}', file=sys.stderr)
        sys.exit(1)
    except ValueError as exc:
        print(f'[错误] {exc}', file=sys.stderr)
        sys.exit(2)

    if args.json:
        print(json.dumps(result_to_dict(result), ensure_ascii=False, indent=2))
    else:
        print_human_readable(result)

    # 有错误时以非零退出码退出，方便 CI 集成
    if result.errors > 0:
        sys.exit(3)


if __name__ == '__main__':
    main()
