"""点「您确认要提交吗？」弹窗里的「确认」按钮 → 等结果 → 截图"""
from __future__ import annotations
import json
import sys
from _debug_utils import screenshot_path
from connect_chrome import get_browser_context


def main():
    with get_browser_context() as ctx:
        target_page = None
        for p in ctx.pages:
            if "PersonnalBatch" in p.url:
                target_page = p
                break
        if not target_page:
            for p in ctx.pages:
                if "oa.example.com" in p.url:
                    target_page = p
                    break

        if not target_page:
            print("❌ 找不到 SHR tab")
            return 1

        page = target_page
        page.bring_to_front()
        print(f"目标 tab: {page.url}")

        # 看弹窗是否还在
        print("\n=== 找 confirm 弹窗里的「确认」按钮 ===")
        try:
            res = page.evaluate("""
                JSON.stringify((function(){
                   var result = [];
                   var btns = document.querySelectorAll('button, a');
                   for (var i = 0; i < btns.length; i++) {
                      var b = btns[i];
                      if (!b.innerText) continue;
                      var t = b.innerText.trim();
                      if (t !== '确认' && t !== '确定') continue;
                      if (b.offsetParent === null) continue;
                      // 排除嵌在 td/grid 里的
                      if (b.closest('td')) continue;
                      // 优先 messenger 类容器里的
                      var inMsg = !!b.closest('.messenger, [class*="messenger"], [class*="modal"], [class*="dialog"]');
                      result.push({tag: b.tagName, id: b.id, cls: (b.className||'').slice(0,80),
                                   text: t, inMsg: inMsg});
                   }
                   return result;
                })())
            """)
            data = json.loads(res) if res else []
            for b in data:
                print(f"  {b}")
        except Exception as e:
            print(f"  ⚠️ {e}")

        # 监听 native dialog
        def on_dialog(d):
            print(f"  🔔 native dialog: {d.message!r}")
            try:
                d.accept()
            except Exception:
                pass
        page.on("dialog", on_dialog)

        # 点击「确认」
        print("\n=== 点击「确认」 ===")
        clicked = page.evaluate("""
            (function(){
               var btns = document.querySelectorAll('button, a');
               for (var i = 0; i < btns.length; i++) {
                  var b = btns[i];
                  if (!b.innerText) continue;
                  var t = b.innerText.trim();
                  if (t !== '确认' && t !== '确定') continue;
                  if (b.offsetParent === null) continue;
                  if (b.closest('td')) continue;
                  // 优先选 messenger 容器里的
                  if (b.closest('.messenger, [class*="messenger"], [class*="modal"], [class*="dialog"]')) {
                     b.click();
                     return 'clicked-messenger';
                  }
               }
               // fallback：随便一个可见的「确认」
               for (var i = 0; i < btns.length; i++) {
                  var b = btns[i];
                  if (!b.innerText) continue;
                  var t = b.innerText.trim();
                  if (t !== '确认' && t !== '确定') continue;
                  if (b.offsetParent === null) continue;
                  if (b.closest('td')) continue;
                  b.click();
                  return 'clicked-fallback';
               }
               return null;
            })()
        """)
        print(f"  结果：{clicked}")

        # 等待提交完成 / 跳转
        page.wait_for_timeout(3500)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(2000)

        print(f"\n提交后 URL: {page.url}")

        # 看 toast / 错误信息
        print("\n=== 提交后页面提示 ===")
        try:
            res = page.evaluate("""
                JSON.stringify((function(){
                   var msgs = [];
                   var sel = '.toast, .messenger-message, .ui-notify, .alert, .successInfo, .errorInfo, .shrtoast, [class*="toast"], [class*="success"], [class*="error"], [class*="message-info"]';
                   var nodes = document.querySelectorAll(sel);
                   for (var i = 0; i < nodes.length; i++) {
                      var n = nodes[i];
                      if (n.offsetParent === null) continue;
                      var t = n.innerText.trim();
                      if (t && t.length < 200) {
                         msgs.push({cls: (n.className||'').slice(0,60), text: t.slice(0,150)});
                      }
                   }
                   return msgs;
                })())
            """)
            data = json.loads(res) if res else []
            if data:
                for m in data:
                    print(f"  {m}")
            else:
                print("  （未发现提示）")
        except Exception as e:
            print(f"  失败：{e}")

        sp = screenshot_path("shr_after_confirm.png")
        page.screenshot(path=sp, full_page=True)
        print(f"\n📸 提交后截图：{sp}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
