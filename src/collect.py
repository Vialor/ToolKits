#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import re
import shutil
import sys


# =========================
# 配置区
# =========================

# 收集后的根目录，必须是绝对路径
# Windows 示例：r"D:\collect_result"
# Git Bash 示例：r"/d/collect_result"
# Linux 示例："/home/me/collect_result"
DEST_ROOT = r"/path/to/collect_result"

# 收集动作：
# "copy" 表示复制
# "move" 表示移动
ACTION = "copy"

# 当目标文件已存在时是否覆盖
OVERWRITE = True

# 是否递归搜索 ROOT 下的所有子目录
RECURSIVE = True

# 正则是否忽略大小写
IGNORE_CASE = True

# 收集规则：
# key：DEST_ROOT 下的文件夹名
# value：规则列表
#
# ROOT：搜索起点目录，必须是绝对路径
# PATTERN：正则表达式，用来匹配路径
# TARGET：
#   "file" 只收集文件
#   "dir" 只收集文件夹
#   "both" 文件和文件夹都收集
COLLECT_MAP = {
    "images": [
        {
            "ROOT": r"D:\data\project",
            "PATTERN": r".*\.(jpg|jpeg|png|gif)$",
            "TARGET": "file",
        },
        {
            "ROOT": r"/home/me/pictures",
            "PATTERN": r"^avatar_.*\.webp$",
            "TARGET": "file",
        },
    ],
    "logs": [
        {
            "ROOT": r"/var/log",
            "PATTERN": r".*\.log$",
            "TARGET": "file",
        },
    ],
    "backup_dirs": [
        {
            "ROOT": r"D:\workspace",
            "PATTERN": r".*backup.*",
            "TARGET": "dir",
        },
    ],
}

# =========================
# 脚本逻辑区
# =========================


def is_absolute_path_str(path_str: str) -> bool:
    """
    判断输入字符串是否是绝对路径。

    支持：
    1. Windows: C:\\xxx 或 C:/xxx
    2. Git Bash: /c/Users/xxx
    3. Linux/macOS: /home/xxx、/var/xxx
    """
    s = path_str.strip()

    # Windows 绝对路径：C:\xxx 或 C:/xxx
    if re.match(r"^[a-zA-Z]:[\\/]", s):
        return True

    # Git Bash 绝对路径：/c/Users/xxx
    if re.match(r"^/[a-zA-Z]/", s):
        return True

    # Linux / macOS 绝对路径：/home/xxx、/var/xxx
    if s.startswith("/"):
        return True

    return False


def normalize_path(path_str: str) -> Path:
    """
    将路径字符串转换为当前 Python 进程可用的 Path。

    支持：
    1. Windows 路径: C:\\xxx\\yyy
    2. Git Bash 路径: /c/xxx/yyy
    3. Linux 路径: /home/xxx/yyy
    """
    s = path_str.strip()

    # Git Bash 风格: /c/Users/xxx -> C:/Users/xxx
    # 只在 Windows 上转换
    if sys.platform.startswith("win"):
        m = re.match(r"^/([a-zA-Z])/(.*)$", s)
        if m:
            drive = m.group(1).upper()
            rest = m.group(2).replace("/", "\\")
            s = f"{drive}:\\{rest}"

    return Path(s).expanduser()


def normalize_path_for_regex(path: Path) -> str:
    """
    将路径转换成适合正则匹配的形式：
    - 统一使用 /
    - 兼容 Windows 和 Linux
    """
    return path.as_posix()


def ensure_valid_action(action: str) -> str:
    action = action.lower().strip()
    if action not in {"copy", "move"}:
        raise ValueError('ACTION 只能是 "copy" 或 "move"')
    return action


def ensure_valid_target(target: str) -> str:
    target = target.lower().strip()
    if target not in {"file", "dir", "both"}:
        raise ValueError('TARGET 只能是 "file"、"dir" 或 "both"')
    return target


def resolve_conflict(target_path: Path, overwrite: bool) -> Path:
    """
    处理目标路径冲突。
    overwrite=True：覆盖原路径。
    overwrite=False：自动生成 xxx_1、xxx_2 这样的新名字。
    """
    if overwrite or not target_path.exists():
        return target_path

    parent = target_path.parent
    stem = target_path.stem
    suffix = target_path.suffix

    index = 1
    while True:
        candidate = parent / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def copy_item(source: Path, target: Path, overwrite: bool) -> Path:
    target = resolve_conflict(target, overwrite)

    if source.is_dir():
        if target.exists() and overwrite:
            shutil.rmtree(target)
        shutil.copytree(source, target)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and overwrite:
            target.unlink()
        shutil.copy2(source, target)

    return target


def move_item(source: Path, target: Path, overwrite: bool) -> Path:
    target = resolve_conflict(target, overwrite)

    if target.exists() and overwrite:
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(target))

    return target


def iter_sources(root: Path, recursive: bool):
    """
    遍历 ROOT 下的文件和文件夹。
    """
    if recursive:
        yield from root.rglob("*")
    else:
        yield from root.iterdir()


def match_rule(path: Path, pattern: re.Pattern, target: str) -> bool:
    """
    同时支持用正则匹配：
    - 文件名
    - 完整路径
    """
    if target == "file" and not path.is_file():
        return False

    if target == "dir" and not path.is_dir():
        return False

    if target == "both" and not (path.is_file() or path.is_dir() or path.is_symlink()):
        return False

    normalized_full_path = normalize_path_for_regex(path)
    normalized_name = path.name

    return bool(
        pattern.search(normalized_full_path)
        or pattern.search(normalized_name)
    )


def validate_dest_root(dest_root_str: str) -> Path:
    """
    校验并转换 DEST_ROOT。
    DEST_ROOT 必须是绝对路径。
    """
    if not is_absolute_path_str(dest_root_str):
        raise ValueError(f"DEST_ROOT 必须是绝对路径：{dest_root_str}")

    return normalize_path(dest_root_str).resolve()


def validate_rule_root(root_str: str) -> Path | None:
    """
    校验并转换规则里的 ROOT。
    ROOT 必须是绝对路径。
    """
    if not is_absolute_path_str(root_str):
        print(f"[跳过] ROOT 不是绝对路径：{root_str}")
        return None

    root = normalize_path(root_str).resolve()

    if not root.exists():
        print(f"[跳过] ROOT 不存在：{root}")
        return None

    if not root.is_dir():
        print(f"[跳过] ROOT 不是文件夹：{root}")
        return None

    return root


def collect_files() -> None:
    action = ensure_valid_action(ACTION)

    dest_root = validate_dest_root(DEST_ROOT)
    dest_root.mkdir(parents=True, exist_ok=True)

    regex_flags = re.IGNORECASE if IGNORE_CASE else 0

    for folder_name, rules in COLLECT_MAP.items():
        dest_folder = dest_root / folder_name
        dest_folder.mkdir(parents=True, exist_ok=True)

        for rule in rules:
            root_str = rule["ROOT"]
            root = validate_rule_root(root_str)

            if root is None:
                continue

            target_type = ensure_valid_target(rule.get("TARGET", "file"))
            pattern = re.compile(rule["PATTERN"], regex_flags)

            for source in iter_sources(root, RECURSIVE):
                if not match_rule(source, pattern, target_type):
                    continue

                target = dest_folder / source.name

                try:
                    if action == "copy":
                        final_target = copy_item(source, target, OVERWRITE)
                        print(f"[复制] {source} -> {final_target}")
                    else:
                        final_target = move_item(source, target, OVERWRITE)
                        print(f"[移动] {source} -> {final_target}")
                except Exception as exc:
                    print(f"[失败] {source}：{exc}")


if __name__ == "__main__":
    collect_files()