#!/usr/bin/env python3
"""! @brief 校验仓库关键文件是否齐全。"""

from __future__ import annotations

from pathlib import Path

REQUIRED = [
    'SKILL.md',
    'README.md',
    'README.en.md',
    'LICENSE',
    'VERSION',
    'scripts/install.py',
    'integrations/gemini/commands/ros-robotics.md',
]


def main() -> None:
    """! @brief CLI 入口。"""
    missing = [item for item in REQUIRED if not Path(item).exists()]
    if missing:
        raise SystemExit(f'缺少关键文件: {missing}')
    print('关键文件检查通过')


if __name__ == '__main__':
    main()
