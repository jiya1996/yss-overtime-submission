"""
debug 脚本共用的工具：跨平台跨用户的截图路径。

为什么不 hardcode `C:\\Users\\<name>\\xxx.png`？
  - 别人电脑没有 sunny 这个用户
  - Mac/Linux 路径分隔符不一样
  - 临时文件不该污染 home

输出路径：
  - Windows：  C:\\Users\\<当前用户>\\AppData\\Local\\Temp\\yss_skill_debug\\
  - Mac/Linux: /tmp/yss_skill_debug/
"""
from __future__ import annotations
import os
import tempfile
from pathlib import Path

_DIR = Path(tempfile.gettempdir()) / "yss_skill_debug"
_DIR.mkdir(exist_ok=True)


def screenshot_path(filename: str) -> str:
    """返回一个用于 page.screenshot(path=...) 的跨平台路径。"""
    return str(_DIR / filename)


if __name__ == "__main__":
    print(f"截图输出目录：{_DIR}")
