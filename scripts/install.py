#!/usr/bin/env python3
"""! @brief 安装 ros-robotics 到 Codex、Claude Code 或 Gemini CLI。"""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

PROJECT_NAME = 'ros-robotics'
RUNTIME_ITEMS = [
    'SKILL.md',
    'README.md',
    'CHANGELOG.md',
    'LICENSE',
    'agents',
    'references',
    'scripts',
    'examples',
    'docs',
]


def codex_skill_dir(home: Path, codex_home_env: str | None = None) -> Path:
    """! @brief 返回 Codex skill 目录。"""
    base = Path(codex_home_env) if codex_home_env else home / '.codex'
    return base / 'skills' / PROJECT_NAME


def claude_skill_dir(home: Path) -> Path:
    """! @brief 返回 Claude Code skill 目录。"""
    return home / '.claude' / 'skills' / PROJECT_NAME


def gemini_command_path(home: Path) -> Path:
    """! @brief 返回 Gemini CLI 命令文件路径。"""
    return home / '.gemini' / 'commands' / f'{PROJECT_NAME}.md'


def detect_default_targets(home: Path) -> list[str]:
    """! @brief 根据本机目录粗略探测默认安装目标。"""
    targets: list[str] = []
    if os.environ.get('CODEX_HOME') or (home / '.codex').exists():
        targets.append('codex')
    if (home / '.claude').exists():
        targets.append('claude')
    if (home / '.gemini').exists():
        targets.append('gemini')
    return targets or ['codex']


def copy_item(source: Path, destination: Path) -> None:
    """! @brief 复制单个文件或目录。"""
    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def install_skill_tree(source_root: Path, destination_root: Path, force: bool) -> None:
    """! @brief 安装 Codex / Claude 可复用 skill 目录。"""
    if destination_root.exists() and force:
        shutil.rmtree(destination_root)
    destination_root.mkdir(parents=True, exist_ok=True)

    for name in RUNTIME_ITEMS:
        source = source_root / name
        if not source.exists():
            continue
        copy_item(source, destination_root / name)


def install_gemini(source_root: Path, destination: Path, force: bool) -> None:
    """! @brief 安装 Gemini CLI 命令文件。"""
    source = source_root / 'integrations' / 'gemini' / 'commands' / f'{PROJECT_NAME}.md'
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not force:
        raise FileExistsError(f'目标已存在：{destination}')
    shutil.copy2(source, destination)


def main() -> None:
    """! @brief CLI 入口。"""
    parser = argparse.ArgumentParser(description='安装 ros-robotics 到不同 Agent 主机')
    parser.add_argument('--target', choices=['auto', 'codex', 'claude', 'gemini', 'all'], default='auto')
    parser.add_argument('--source-root', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()

    source_root = Path(args.source_root).resolve()
    home = Path.home()

    if args.target == 'auto':
        targets = detect_default_targets(home)
    elif args.target == 'all':
        targets = ['codex', 'claude', 'gemini']
    else:
        targets = [args.target]

    for target in targets:
        if target == 'codex':
            destination = codex_skill_dir(home, os.environ.get('CODEX_HOME'))
            install_skill_tree(source_root, destination, args.force)
            print(f'[codex] 已安装到: {destination}')
        elif target == 'claude':
            destination = claude_skill_dir(home)
            install_skill_tree(source_root, destination, args.force)
            print(f'[claude] 已安装到: {destination}')
        elif target == 'gemini':
            destination = gemini_command_path(home)
            install_gemini(source_root, destination, args.force)
            print(f'[gemini] 已安装到: {destination}')


if __name__ == '__main__':
    main()
