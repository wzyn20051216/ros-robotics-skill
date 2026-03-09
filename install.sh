#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/wzyn20051216/ros-robotics-skill.git"
BRANCH="${ROS_ROBOTICS_BRANCH:-main}"
TARGET="${ROS_ROBOTICS_TARGET:-auto}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="$2"
      shift 2
      ;;
    --branch)
      BRANCH="$2"
      shift 2
      ;;
    *)
      echo "未知参数: $1" >&2
      exit 1
      ;;
  esac
done

command -v git >/dev/null 2>&1 || { echo "需要 git" >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "需要 python3" >&2; exit 1; }

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$TMP_DIR/ros-robotics-skill" >/dev/null 2>&1
python3 "$TMP_DIR/ros-robotics-skill/scripts/install.py" --source-root "$TMP_DIR/ros-robotics-skill" --target "$TARGET" --force
