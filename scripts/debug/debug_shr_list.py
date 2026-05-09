"""
Debug 第二步：从空白表单页点「奋斗列表」按钮进入真实列表页，dump DOM
"""
from __future__ import annotations
import sys
from _debug_utils import screenshot_path
from connect_chrome import find_or_open_tab, get_browser_context
from selectors import SHR_BILL_LIST_URL


def main():
    with get_browser_context() as ctx:
        page = find_or_open_tab(ctx, "https://oa.example.com", SHR_BILL_LIST_URL)
        page.goto(SHR_BILL_LIST_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        page.wait_for_timeout(1500)

        print(f"Step1 URL: {page.url}")
        print(f"Step1 Title: {page.title()}")

        # 1. 找并点击「奋斗列表」
        print("\n=== Step1 寻找并点击「奋斗列表」按钮 ===")
        loc = page.get_by_text("奋斗列表", exact=True)
        try:
            cnt = loc.count()
            print(f"  匹配 {cnt} 个元素")
            if cnt == 0:
                print("  ❌ 没找到「奋斗列表」按钮，可能页面没加载完")
                return 1
        except Exception as e:
            print(f"  count 失败：{e}")
            return 1

        # 多种点击策略尝试
        clicked = False
        # 尝试 1：scroll into view + 普通 click
        try:
            page.locator("#returnToOverTimeBillList").scroll_into_view_if_needed(timeout=3000)
            page.locator("#returnToOverTimeBillList").click(timeout=3000)
            print("  ✅ 普通点击成功")
            clicked = True
        except Exception as e:
            print(f"  ⚠️  普通点击失败：{type(e).__name__}: {str(e)[:120]}")

        # 尝试 2：force click
        if not clicked:
            try:
                page.locator("#returnToOverTimeBillList").click(force=True, timeout=3000)
                print("  ✅ force click 成功")
                clicked = True
            except Exception as e:
                print(f"  ⚠️  force click 失败：{type(e).__name__}: {str(e)[:120]}")

        # 尝试 3：JS click
        if not clicked:
            try:
                page.evaluate("document.getElementById('returnToOverTimeBillList').click()")
                print("  ✅ JS click 触发")
                clicked = True
            except Exception as e:
                print(f"  ❌ JS click 失败：{e}")
                return 1

        if not clicked:
            return 1

        page.wait_for_timeout(3000)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(2000)

        # 2. 现在到列表页
        print(f"\nStep2 URL: {page.url}")

        sp = screenshot_path("shr_list.png")
        page.screenshot(path=sp, full_page=True)
        print(f"📸 截图: {sp}")

        # 3. dump frame 列表
        print("\n=== frames ===")
        for i, fr in enumerate(page.frames):
            print(f"  [{i}] name={fr.name!r}  url={fr.url[:120]}")

        # 4. 用 evaluate 拿 DOM 信息（简单返回 JSON）
        # 关键：JS 表达式末尾 return 一个 JSON-serializable 值
        print("\n=== 顶部按钮（前 60 个可见短文本元素）===")
        try:
            res = page.evaluate("""
                JSON.stringify(
                  Array.from(document.querySelectorAll('button, a, span, div'))
                    .filter(function(el){
                       return el.offsetParent !== null &&
                              el.innerText &&
                              el.innerText.trim().length > 0 &&
                              el.innerText.trim().length < 8;
                    })
                    .slice(0, 80)
                    .map(function(el){
                       return {tag: el.tagName, text: el.innerText.trim(), cls: (el.className||'').slice(0,50)};
                    })
                )
            """)
            import json
            data = json.loads(res) if res else []
            seen = set()
            for b in data:
                if b['text'] in seen:
                    continue
                seen.add(b['text'])
                print(f"  [{b['tag']:6}] {b['text']:8} cls={b['cls']}")
        except Exception as e:
            print(f"  评估失败：{e}")

        # 5. 所有 input
        print("\n=== 所有可见 input ===")
        try:
            res = page.evaluate("""
                JSON.stringify(
                  Array.from(document.querySelectorAll('input'))
                    .filter(function(el){return el.offsetParent !== null;})
                    .slice(0, 40)
                    .map(function(el){
                       return {type: el.type, name: el.name, id: el.id,
                               placeholder: el.placeholder,
                               cls: (el.className||'').slice(0,40),
                               val: (el.value||'').slice(0,30)};
                    })
                )
            """)
            import json
            data = json.loads(res) if res else []
            for inp in data:
                print(f"  {inp}")
        except Exception as e:
            print(f"  失败：{e}")

        # 6. 表格行（前 5 行）
        print("\n=== 表格行（前 5 行）===")
        try:
            res = page.evaluate("""
                JSON.stringify((function(){
                  var result = [];
                  var tables = document.querySelectorAll('table');
                  for (var ti = 0; ti < tables.length; ti++) {
                     var trs = tables[ti].querySelectorAll('tr');
                     for (var ri = 0; ri < trs.length; ri++) {
                        var tr = trs[ri];
                        var tds = tr.querySelectorAll('td');
                        if (tds.length < 3) continue;
                        var cells = [];
                        for (var ci = 0; ci < Math.min(tds.length, 14); ci++) {
                           cells.push(tds[ci].innerText.trim().slice(0, 30));
                        }
                        result.push({tableIdx: ti, cls: tr.className, cells: cells});
                        if (result.length >= 5) return result;
                     }
                  }
                  return result;
                })())
            """)
            import json
            data = json.loads(res) if res else []
            for r in data:
                print(f"  table[{r['tableIdx']}] cls={r['cls']!r}")
                for j, c in enumerate(r['cells']):
                    print(f"     td[{j:2}] = {c!r}")
                print()
        except Exception as e:
            print(f"  失败：{e}")

        # 7. 表头（找出列名顺序，方便定位列 index）
        print("\n=== 表头（th 文本）===")
        try:
            res = page.evaluate("""
                JSON.stringify((function(){
                  var result = [];
                  var tables = document.querySelectorAll('table');
                  for (var ti = 0; ti < tables.length; ti++) {
                     var ths = tables[ti].querySelectorAll('th');
                     if (ths.length === 0) continue;
                     var hdrs = [];
                     for (var i = 0; i < ths.length; i++) {
                        hdrs.push(ths[i].innerText.trim().slice(0, 20));
                     }
                     result.push({tableIdx: ti, hdrs: hdrs});
                  }
                  return result;
                })())
            """)
            import json
            data = json.loads(res) if res else []
            for r in data:
                print(f"  table[{r['tableIdx']}] 表头：")
                for j, h in enumerate(r['hdrs']):
                    print(f"     th[{j:2}] = {h!r}")
        except Exception as e:
            print(f"  失败：{e}")

        return 0


if __name__ == "__main__":
    sys.exit(main())
