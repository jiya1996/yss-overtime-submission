"""
Debug 第四步：查询本周已提交奋斗单 + dump 表格内容
"""
from __future__ import annotations
import json
import sys
from _debug_utils import screenshot_path
from connect_chrome import find_or_open_tab, get_browser_context
from selectors import SHR_BILL_LIST_URL


def main():
    with get_browser_context() as ctx:
        page = find_or_open_tab(ctx, "https://oa.example.com", SHR_BILL_LIST_URL)
        page.goto(SHR_BILL_LIST_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(1500)

        # 1. 展开筛选（如果没展开）
        try:
            page.get_by_text("展开筛选", exact=True).first.click(timeout=3000)
            print("展开了筛选")
        except Exception:
            print("筛选可能已经展开")

        page.wait_for_timeout(800)

        # 2. 设置日期：5/6 - 5/7（覆盖更精确范围）
        # 先选「自定义」
        try:
            # 直接 fill 起止日期
            page.locator("#entries--otDate-datestart").fill("2026-05-06")
            page.locator("#entries--otDate-dateend").fill("2026-05-07")
            print("已填日期 5/6 - 5/7")
        except Exception as e:
            print(f"⚠️  填日期失败：{e}")

        page.wait_for_timeout(500)

        # 3. 点查询
        try:
            page.locator("#filter-search").click(timeout=5000)
            print("✅ 已点查询")
        except Exception as e:
            print(f"❌ 查询点击失败：{e}")
            return 1

        page.wait_for_timeout(2500)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        page.wait_for_timeout(1000)

        # 4. 抓 jqGrid 数据行
        # jqGrid 数据行 selector：tr.jqgrow 或 #grid 后代 tr
        print("\n=== 查询后表格行（jqgrow）===")
        try:
            res = page.evaluate("""
                JSON.stringify((function(){
                   var rows = document.querySelectorAll('tr.jqgrow');
                   var result = [];
                   for (var i = 0; i < rows.length; i++) {
                      var tds = rows[i].querySelectorAll('td');
                      var cells = [];
                      for (var j = 0; j < tds.length; j++) {
                         cells.push(tds[j].innerText.trim().slice(0, 40));
                      }
                      result.push({idx: i, id: rows[i].id, cells: cells});
                   }
                   return result;
                })())
            """)
            data = json.loads(res) if res else []
            print(f"  找到 {len(data)} 行")
            for r in data:
                print(f"  row[{r['idx']}] id={r['id']}")
                for j, c in enumerate(r['cells']):
                    if c:
                        print(f"     td[{j:2}] = {c!r}")
                print()
        except Exception as e:
            print(f"  失败：{e}")

        # 5. 同时看「无数据」提示
        try:
            empty = page.evaluate("""
                (function(){
                   var el = document.querySelector('#emptyResult, .ui-paging-info');
                   return el ? el.innerText : null;
                })()
            """)
            print(f"  分页/空提示文本：{empty!r}")
        except Exception:
            pass

        sp = screenshot_path("shr_query.png")
        page.screenshot(path=sp, full_page=True)
        print(f"📸 截图：{sp}")

        return 0


if __name__ == "__main__":
    sys.exit(main())
