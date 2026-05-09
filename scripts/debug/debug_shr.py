"""
Debug 脚本：导航到 SHR 奋斗单列表页，dump iframe 结构 + 关键 DOM 给我看
=========================================================================
"""
from __future__ import annotations
import sys
from _debug_utils import screenshot_path
from connect_chrome import find_or_open_tab, get_browser_context
from selectors import SHR_BILL_LIST_URL


def main():
    with get_browser_context() as ctx:
        page = find_or_open_tab(ctx, "https://oa.example.com", SHR_BILL_LIST_URL)

        print(f"➡️  goto: {SHR_BILL_LIST_URL}")
        page.goto(SHR_BILL_LIST_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)  # 给 iframe 加载留时间
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(2000)

        print(f"📍 当前 URL: {page.url}")
        print(f"📍 页面标题: {page.title()}")

        # 1. 列出所有 frame
        print("\n=== 全部 frame 列表 ===")
        for i, fr in enumerate(page.frames):
            print(f"  [{i}] name={fr.name!r:30} url={fr.url[:120]}")

        # 2. 截图
        sp = screenshot_path("shr_debug.png")
        page.screenshot(path=sp, full_page=True)
        print(f"\n📸 已保存截图：{sp}")

        # 3. dump 主 frame 的 body 前 4000 字符
        try:
            body_html = page.evaluate("() => document.body ? document.body.outerHTML : ''")
            print(f"\n=== 主 frame body 长度 = {len(body_html)} ===")
            print(body_html[:4000])
            print("…" if len(body_html) > 4000 else "")
        except Exception as e:
            print(f"主 frame dump 失败：{e}")

        # 4. 对每个 iframe 也 dump
        for i, fr in enumerate(page.frames):
            if fr == page.main_frame:
                continue
            try:
                # 只 dump 看起来跟业务相关的（URL 包含 example 或 shr 或 ats）
                if not any(k in fr.url for k in ("example", "shr", "ats", "kingdee", "OverTime")):
                    print(f"\n--- iframe[{i}] 跳过（URL 不像业务页）---")
                    continue
                html = fr.evaluate("() => document.body ? document.body.outerHTML : ''")
                print(f"\n=== iframe[{i}] url={fr.url[:120]} 长度 = {len(html)} ===")
                print(html[:3000])
                print("…" if len(html) > 3000 else "")
            except Exception as e:
                print(f"iframe[{i}] dump 失败：{e}")

        # 5. 找页面里所有 input + button 的关键属性
        print("\n=== 主 frame 所有 input ===")
        inputs = page.evaluate("""
            () => Array.from(document.querySelectorAll('input')).slice(0, 30).map(el => ({
                type: el.type, name: el.name, id: el.id,
                placeholder: el.placeholder, cls: el.className,
                visible: el.offsetParent !== null
            }))
        """)
        for inp in inputs:
            print(f"  {inp}")

        print("\n=== 主 frame 所有按钮文本 ===")
        btns = page.evaluate("""
            () => Array.from(document.querySelectorAll('button, a, span'))
                    .filter(el => el.offsetParent !== null && el.innerText && el.innerText.length < 20)
                    .slice(0, 60)
                    .map(el => ({tag: el.tagName, text: el.innerText.trim(), cls: el.className}))
        """)
        for b in btns:
            print(f"  {b}")


if __name__ == "__main__":
    sys.exit(main() or 0)
