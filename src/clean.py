#!/usr/bin/env python3 
# -*- coding: utf-8 -*-

from pathlib import Path
import shutil
import re
import sys


# ======== 配置 ========

# 是否只预览，不真正删除
DRY_RUN = False

# 是否递归搜索 ROOT 下的所有子目录
RECURSIVE = True

# 正则是否忽略大小写
IGNORE_CASE = True

# 删除规则：
# ROOT：从哪个目录开始搜索，必须是绝对路径
# PATTERN：正则表达式
# TARGET：
#   "file" 只删除文件
#   "dir" 只删除目录
#   "both" 文件和目录都删除
#
# 注意：
# - 正则会同时匹配完整路径和文件名
# - 路径会统一成 / 再匹配，所以 Windows 路径也可以用 / 写正则
DELETE_RULES = [
    {
        "ROOT": r"C:\Users",
        "PATTERN": r"case_001$",
        "TARGET": "dir",
    },
]

# =====================


def is_absolute_path_str(path_str: str) -> bool:
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
    return path.as_posix()


def ensure_valid_target(target: str) -> str:
    target = target.lower().strip()
    if target not in {"file", "dir", "both"}:
        raise ValueError('TARGET 只能是 "file"、"dir" 或 "both"')
    return target


def iter_candidates(root: Path, recursive: bool):
    """
    遍历 ROOT 下的候选文件和文件夹。
    """
    if recursive:
        yield from root.rglob("*")
    else:
        yield from root.iterdir()


def match_target_type(path: Path, target: str) -> bool:
    """
    判断候选项类型是否符合 TARGET。

    注意：
    - 符号链接统一按“可删除对象”处理。
    - 如果 TARGET="file"，文件链接通常也会被视为文件或 symlink。
    - 如果 TARGET="dir"，目录链接是否被 is_dir() 识别，取决于系统和链接目标。
    """
    if target == "file":
        return path.is_file() or path.is_symlink()

    if target == "dir":
        return path.is_dir() or path.is_symlink()

    if target == "both":
        return path.is_file() or path.is_dir() or path.is_symlink()

    return False


def match_rule(path: Path, pattern: re.Pattern, target: str) -> bool:
    """
    同时支持用正则匹配：
    - 文件名 / 文件夹名
    - 完整路径
    """
    if not match_target_type(path, target):
        return False

    normalized_full_path = normalize_path_for_regex(path)
    normalized_name = path.name

    return bool(
        pattern.search(normalized_full_path)
        or pattern.search(normalized_name)
    )


def delete_path(path: Path) -> None:
    try:
        if not path.exists() and not path.is_symlink():
            print(f"[SKIP] 不存在: {path}")
            return

        if DRY_RUN:
            print(f"[DRY] 将删除: {path}")
            return

        if path.is_symlink():
            path.unlink()
            print(f"[OK] 已删除链接: {path}")
        elif path.is_file():
            path.unlink()
            print(f"[OK] 已删除文件: {path}")
        elif path.is_dir():
            shutil.rmtree(path)
            print(f"[OK] 已删除目录: {path}")
        else:
            print(f"[SKIP] 未知类型: {path}")

    except Exception as e:
        print(f"[ERR] 删除失败: {path} -> {e}")


def run_delete_rule(rule: dict, regex_flags: int) -> None:
    root_str = rule["ROOT"]
    pattern_str = rule["PATTERN"]
    target = ensure_valid_target(rule.get("TARGET", "both"))

    if not is_absolute_path_str(root_str):
        print(f"[SKIP] ROOT 不是绝对路径: {root_str}")
        return

    root = normalize_path(root_str)

    if not root.exists():
        print(f"[SKIP] ROOT 不存在: {root}")
        return

    if not root.is_dir():
        print(f"[SKIP] ROOT 不是目录: {root}")
        return

    pattern = re.compile(pattern_str, regex_flags)

    matched_paths = []

    for candidate in iter_candidates(root, RECURSIVE):
        if match_rule(candidate, pattern, target):
            matched_paths.append(candidate)

    if not matched_paths:
        print(f"[INFO] 未匹配到内容: ROOT={root}, PATTERN={pattern_str}")
        return

    # 目录删除时，先删除更深层的路径，避免父目录先删导致子路径不存在
    matched_paths.sort(
        key=lambda p: len(p.parts),
        reverse=True,
    )

    for path in matched_paths:
        delete_path(path)


def main() -> None:
    regex_flags = re.IGNORECASE if IGNORE_CASE else 0

    for rule in DELETE_RULES:
        run_delete_rule(rule, regex_flags)


if __name__ == "__main__":
    main()