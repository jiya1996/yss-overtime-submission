"""
连接到用户已登录的 Chrome (通过 CDP)
======================================

使用前提：用户已经按 references/chrome_setup.md 启动了 debug 模式 Chrome。
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Optional

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright


CDP_ENDPOINT = "http://localhost:9222"


@contextmanager
def get_browser_context() -> Iterator[BrowserContext]:
    """连接到已登录 Chrome 并返回 BrowserContext。

    用法：
        with get_browser_context() as ctx:
            page = ctx.new_page()
            page.goto("https://...")
    """
    with sync_playwright() as p:
        try:
            browser: Browser = p.chromium.connect_over_cdp(CDP_ENDPOINT)
        except Exception as e:
            raise RuntimeError(
                f"❌ 无法连接到 Chrome 调试端口 {CDP_ENDPOINT}\n"
                "   请检查：\n"
                "   1. Chrome 是否用 --remote-debugging-port=9222 启动\n"
                "   2. 是否有其他 Chrome 进程占用端口\n"
                "   详见 references/chrome_setup.md"
            ) from e

        if not browser.contexts:
            raise RuntimeError(
                "❌ Chrome 没有任何打开的窗口/标签页。\n"
                "   请在 debug Chrome 里至少开一个 tab 后重试。"
            )

        # 复用第一个 context（用户已登录的那个）
        context = browser.contexts[0]
        try:
            yield context
        finally:
            # 不关闭 browser！否则用户的 Chrome 也会一起关
            pass


def find_or_open_tab(context: BrowserContext, url_prefix: str,
                     fallback_url: Optional[str] = None) -> Page:
    """在已打开的标签页里找以 url_prefix 开头的，找不到就新开。

    Args:
        context: BrowserContext
        url_prefix: 用于匹配现有 tab，例如 "https://pm.example.com"
        fallback_url: 找不到时新开 tab 用的完整 URL（默认 = url_prefix）
    """
    for page in context.pages:
        if page.url.startswith(url_prefix):
            page.bring_to_front()
            return page

    page = context.new_page()
    page.goto(fallback_url or url_prefix)
    return page


if __name__ == "__main__":
    # 自检：连进去看看有几个 tab，分别是什么 URL
    with get_browser_context() as ctx:
        print(f"✅ 连接成功，当前 {len(ctx.pages)} 个 tab：")
        for i, p in enumerate(ctx.pages):
            title = p.title()[:50] if p.title() else "(无标题)"
            print(f"  [{i}] {p.url[:80]}  | {title}")
