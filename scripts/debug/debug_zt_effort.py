"""
Debug 禅道工时确认页结构（用户给的真实 URL）
================================================

URL: https://pm.example.com:8071/index.php?m=todo&f=confirmuserconsumed
"""
from __future__ import annotations
import json
import sys
from _debug_utils import screenshot_path
from connect_chrome import find_or_open_tab, get_browser_context

ZT_EFFORT_URL_REAL = "https://pm.example.com:8071/index.php?m=todo&f=confirmuserconsumed"


def main():
    target_date = "2026-05-06"

    with get_browser_context() as ctx:
        page = find_or_open_tab(ctx, "https://pm.example.com", ZT_EFFORT_URL_REAL)
        page.goto(ZT_EFFORT_URL_REAL, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        page.wait_for_timeout(1000)

        print(f"URL: {page.url}")
        print(f"Title: {page.title()}")

        # 1. 截图初始状态
        sp_init = screenshot_path("zt_effort_initial.png")
        page.screenshot(path=sp_init, full_page=True)
        print(f"📸 初始截图：{sp_init}")

        # 2. 找日期选择器
        print("\n=== 所有可见 input ===")
        try:
            res = page.evaluate("""
                JSON.stringify(
                  Array.from(document.querySelectorAll('input'))
                    .filter(function(el){return el.offsetParent !== null;})
                    .slice(0, 30)
                    .map(function(el){
                       return {type: el.type, name: el.name, id: el.id,
                               placeholder: el.placeholder,
                               cls: (el.className||'').slice(0,50),
                               val: (el.value||'').slice(0,30)};
                    })
                )
            """)
            data = json.loads(res) if res else []
            for inp in data:
                print(f"  {inp}")
        except Exception as e:
            print(f"失败: {e}")

        # 3. 找日期相关文本（"项目耗时日历" 标签等）
        print("\n=== 找「项目耗时日历」附近 ===")
        try:
            res = page.evaluate("""
                JSON.stringify((function(){
                   var nodes = document.querySelectorAll('span, label, div, td');
                   for (var i = 0; i < nodes.length; i++) {
                      var n = nodes[i];
                      if (n.innerText && n.innerText.trim().indexOf('项目耗时日历') !== -1
                          && n.offsetParent !== null && n.children.length < 4) {
                         var p = n.parentElement;
                         return {tag: n.tagName, text: n.innerText.trim().slice(0,50),
                                 parent_html: p ? p.outerHTML.slice(0, 1000) : null};
                      }
                   }
                   return null;
                })())
            """)
            data = json.loads(res) if res else None
            if data:
                print(f"  {data['tag']}: {data['text']!r}")
                print(f"  parent_html:")
                print(data['parent_html'])
            else:
                print("  没找到「项目耗时日历」")
        except Exception as e:
            print(f"失败: {e}")

        # 4. 尝试切换日期：找 input + 填 + 触发
        print(f"\n=== 尝试切换日期到 {target_date} ===")
        try:
            # 找日期 input
            date_input = page.locator('input[name="date"], input[type="date"], input.date-input, input[placeholder*="日期"]').first
            if date_input.count() > 0:
                date_input.fill(target_date)
                date_input.press("Enter")
                print("  ✅ 填了日期 + Enter")
            else:
                print("  ⚠️  没找到日期 input，尝试备选")
        except Exception as e:
            print(f"  ⚠️  失败：{e}")

        page.wait_for_timeout(2000)

        # 5. dump 表头 + 数据行
        print("\n=== 表格表头（th）===")
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
                         hdrs.push(ths[i].innerText.trim().slice(0, 30));
                      }
                      result.push({tableIdx: ti, hdrs: hdrs, cls: tables[ti].className});
                   }
                   return result;
                })())
            """)
            data = json.loads(res) if res else []
            for r in data:
                print(f"  table[{r['tableIdx']}] cls={r['cls']!r}")
                for j, h in enumerate(r['hdrs']):
                    print(f"     th[{j:2}] = {h!r}")
        except Exception as e:
            print(f"失败: {e}")

        print("\n=== 数据行（前 5 行）===")
        try:
            res = page.evaluate("""
                JSON.stringify((function(){
                   var result = [];
                   var trs = document.querySelectorAll('table tbody tr');
                   for (var i = 0; i < trs.length && result.length < 5; i++) {
                      var tds = trs[i].querySelectorAll('td');
                      if (tds.length < 3) continue;
                      var cells = [];
                      for (var j = 0; j < tds.length; j++) {
                         var t = tds[j].innerText.trim();
                         var input = tds[j].querySelector('input[type="text"], textarea');
                         if (input) t += '  [input val="' + (input.value||'').slice(0,40) + '"]';
                         cells.push(t.slice(0, 80));
                      }
                      result.push({idx: i, cls: trs[i].className, cells: cells});
                   }
                   return result;
                })())
            """)
            data = json.loads(res) if res else []
            print(f"  共 {len(data)} 行（限前 5）")
            for r in data:
                print(f"  row[{r['idx']}] cls={r['cls']!r}")
                for j, c in enumerate(r['cells']):
                    if c:
                        print(f"     td[{j:2}] = {c!r}")
                print()
        except Exception as e:
            print(f"失败: {e}")

        sp_after = screenshot_path("zt_effort_after.png")
        page.screenshot(path=sp_after, full_page=True)
        print(f"📸 切日期后截图：{sp_after}")

        return 0


if __name__ == "__main__":
    sys.exit(main())
