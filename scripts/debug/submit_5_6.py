"""
点提交按钮：找到已经填好的 multi-create tab → 点顶部「提交」 → 等响应 → 截图
==========================================================================

⚠️ 不会 goto 任何 URL，避免重置已填好的表单！
"""
from __future__ import annotations
import json
import sys
from _debug_utils import screenshot_path
from connect_chrome import get_browser_context


def main():
    with get_browser_context() as ctx:
        # 找到 multi-create 那个 tab（不要 goto）
        target_page = None
        for p in ctx.pages:
            if "PersonnalBatch" in p.url:
                target_page = p
                break

        if not target_page:
            # fallback：找 SHR 相关 tab
            for p in ctx.pages:
                if "oa.example.com" in p.url and "OverTime" in p.url:
                    target_page = p
                    break

        if not target_page:
            print("❌ 没找到 multi-create tab。可能页面被关了。")
            return 1

        page = target_page
        page.bring_to_front()
        print(f"找到目标 tab：{page.url}")
        print(f"Title：{page.title()}")

        # 1. 提交前截图（最后一次确认）
        sp_pre = screenshot_path("shr_pre_submit.png")
        page.screenshot(path=sp_pre, full_page=True)
        print(f"📸 提交前截图：{sp_pre}")

        # 2. 监听 dialog（金蝶可能弹 confirm）
        dialogs_seen = []
        def on_dialog(dialog):
            print(f"  🔔 弹窗：type={dialog.type} message={dialog.message!r}")
            dialogs_seen.append(dialog.message)
            try:
                dialog.accept()
            except Exception:
                pass
        page.on("dialog", on_dialog)

        # 3. 找顶部「提交」按钮
        # multi-create 页顶部有「提交」「奋斗列表」两个按钮
        # 排除单元格里的「提交」
        print("\n=== 找顶部「提交」按钮 ===")
        try:
            res = page.evaluate("""
                JSON.stringify((function(){
                   var btns = document.querySelectorAll('button, a');
                   var result = [];
                   for (var i = 0; i < btns.length; i++) {
                      var b = btns[i];
                      if (!b.innerText) continue;
                      if (b.innerText.trim() !== '提交') continue;
                      if (b.offsetParent === null) continue;
                      // 排除嵌在 td 里的（cell content）
                      var inTd = !!b.closest('td');
                      result.push({tag: b.tagName, id: b.id,
                                   cls: (b.className||'').slice(0,80),
                                   inTd: inTd, name: b.name});
                   }
                   return result;
                })())
            """)
            data = json.loads(res) if res else []
            for b in data:
                print(f"  {b}")
        except Exception as e:
            print(f"  失败：{e}")

        # 4. 点击顶部「提交」（不在 td 里的那个）
        print("\n=== 点击顶部「提交」 ===")
        try:
            clicked = page.evaluate("""
                (function(){
                   var btns = document.querySelectorAll('button, a');
                   for (var i = 0; i < btns.length; i++) {
                      var b = btns[i];
                      if (!b.innerText) continue;
                      if (b.innerText.trim() !== '提交') continue;
                      if (b.offsetParent === null) continue;
                      if (b.closest('td')) continue;
                      b.click();
                      return {clicked: true, tag: b.tagName, id: b.id, cls: (b.className||'').slice(0,80)};
                   }
                   return {clicked: false};
                })()
            """)
            print(f"  结果：{clicked}")
        except Exception as e:
            print(f"  ❌ 点击失败：{e}")
            return 1

        # 5. 等响应
        page.wait_for_timeout(3000)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(2000)

        print(f"\n提交后 URL：{page.url}")

        # 6. 看页面里有没有 toast / 提示文本
        print("\n=== 提交后页面提示 ===")
        try:
            res = page.evaluate("""
                JSON.stringify((function(){
                   var msgs = [];
                   // 常见提示容器
                   var sel = '.toast, .ui-notify, .alert, .ant-message, .layui-layer-msg, .successInfo, .errorInfo, .shrtoast, [class*="toast"], [class*="success"]';
                   var nodes = document.querySelectorAll(sel);
                   for (var i = 0; i < nodes.length; i++) {
                      var n = nodes[i];
                      if (n.offsetParent === null) continue;
                      var t = n.innerText.trim();
                      if (t && t.length < 200) msgs.push({cls: n.className.slice(0,60), text: t});
                   }
                   return msgs;
                })())
            """)
            data = json.loads(res) if res else []
            if data:
                for m in data:
                    print(f"  {m}")
            else:
                print("  （未发现明显提示元素）")
        except Exception as e:
            print(f"  失败：{e}")

        # 7. 收集 dialog
        if dialogs_seen:
            print("\n=== 触发的 native dialog ===")
            for d in dialogs_seen:
                print(f"  {d!r}")

        # 8. 最终截图
        sp_post = screenshot_path("shr_post_submit.png")
        page.screenshot(path=sp_post, full_page=True)
        print(f"\n📸 提交后截图：{sp_post}")

        return 0


if __name__ == "__main__":
    sys.exit(main())
