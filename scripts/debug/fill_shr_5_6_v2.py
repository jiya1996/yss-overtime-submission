"""
完整填表：奋斗日期、奋斗积分（下拉 1.5）、备注（占位）
======================================================================
停在「提交」按钮前，截图等用户确认。
"""
from __future__ import annotations
import json
import sys
from _debug_utils import screenshot_path
from connect_chrome import find_or_open_tab, get_browser_context

MULTI_CREATE_URL = (
    "https://oa.example.com:5887/shr/dynamic.do"
    "?uipk=com.kingdee.eas.hr.ats.app.AtsOverTimeBillForm.PersonnalBatch"
    "&inFrame=true&billId=&method=addNew"
)

TARGET_DATE = "2026-05-06"
TARGET_POINTS = "1.5"
TARGET_DESC = "<your work content>"


def main():
    with get_browser_context() as ctx:
        page = find_or_open_tab(ctx, "https://oa.example.com", MULTI_CREATE_URL)
        page.goto(MULTI_CREATE_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        try:
            page.wait_for_load_state("networkidle", timeout=12000)
        except Exception:
            pass
        page.wait_for_timeout(1500)

        # 1. 点新增
        print("Step 1: 点「新增」")
        page.evaluate("document.getElementById('addRow_entries').click()")
        page.wait_for_timeout(1500)

        # 2. 填奋斗日期
        print(f"Step 2: 填奋斗日期 {TARGET_DATE}")
        try:
            page.locator('td[aria-describedby="entries_otDate"]').first.click(timeout=3000)
            page.wait_for_timeout(500)
            otdate_inp = page.locator('td[aria-describedby="entries_otDate"] input').first
            otdate_inp.fill(TARGET_DATE)
            otdate_inp.press("Tab")
            page.wait_for_timeout(1500)
            print("  ✅ 奋斗日期已填")
        except Exception as e:
            print(f"  ⚠️ 失败：{e}")

        # 3. 填奋斗积分（下拉，选 1.5）
        print(f"Step 3: 选奋斗积分 {TARGET_POINTS}")
        try:
            # 点开奋斗积分单元格
            page.locator('td[aria-describedby="entries_strugglePoints"]').first.click(timeout=3000)
            page.wait_for_timeout(800)
            # dump 一下当前下拉是否出现
            dropdown_info = page.evaluate("""
                JSON.stringify((function(){
                   // 找 visible 的 dropdown 列表
                   var lists = document.querySelectorAll('ul.dropdown-menu, .select2-results, .combo-list, ul[role="listbox"], .el-select-dropdown__list, ul.selectListUl');
                   for (var i = 0; i < lists.length; i++) {
                      var l = lists[i];
                      if (l.offsetParent !== null) {
                         var items = l.querySelectorAll('li, .item, option');
                         var texts = [];
                         for (var j = 0; j < items.length && j < 20; j++) {
                            texts.push(items[j].innerText.trim().slice(0, 20));
                         }
                         return {tag: l.tagName, cls: l.className.slice(0,60),
                                 itemCount: items.length, texts: texts};
                      }
                   }
                   return null;
                })())
            """)
            data = json.loads(dropdown_info) if dropdown_info else None
            print(f"  下拉信息：{data}")

            # 点选 1.5
            page.evaluate("""
                (function(){
                   var lists = document.querySelectorAll('ul.dropdown-menu, ul[role="listbox"], ul.selectListUl, .combo-list, .select2-results');
                   for (var i = 0; i < lists.length; i++) {
                      var l = lists[i];
                      if (l.offsetParent === null) continue;
                      var items = l.querySelectorAll('li, .item, option, a');
                      for (var j = 0; j < items.length; j++) {
                         var t = items[j].innerText.trim();
                         if (t === '1.5') {
                            items[j].click();
                            return 'clicked: ' + t;
                         }
                      }
                   }
                   return 'no match';
                })()
            """)
            page.wait_for_timeout(800)
            print("  ✅ 已点选 1.5")
        except Exception as e:
            print(f"  ⚠️ 失败：{e}")

        page.wait_for_timeout(1000)

        # 4. 填备注（奋斗内容）
        print(f"Step 4: 填备注 「{TARGET_DESC}」")
        try:
            page.locator('td[aria-describedby="entries_description"]').first.click(timeout=3000)
            page.wait_for_timeout(500)
            desc_inp = page.locator('td[aria-describedby="entries_description"] input, td[aria-describedby="entries_description"] textarea').first
            desc_inp.fill(TARGET_DESC)
            desc_inp.press("Tab")
            page.wait_for_timeout(800)
            print("  ✅ 备注已填")
        except Exception as e:
            print(f"  ⚠️ 失败：{e}")

        page.wait_for_timeout(1500)

        # 5. 截图当前完整状态
        sp = screenshot_path("shr_filled_full.png")
        page.screenshot(path=sp, full_page=True)
        print(f"\n📸 完整截图：{sp}")

        # 6. dump 当前行所有 cell 显示文本
        print("\n=== 最终行状态 ===")
        res = page.evaluate("""
            JSON.stringify((function(){
               var trs = document.querySelectorAll('tr.jqgrow');
               for (var i = 0; i < trs.length; i++) {
                  var tr = trs[i];
                  if ((tr.className||'').indexOf('jqgfirstrow') >= 0) continue;
                  var tds = tr.querySelectorAll('td');
                  if (tds.length < 5) continue;
                  var info = {};
                  for (var j = 0; j < tds.length; j++) {
                     var aria = tds[j].getAttribute('aria-describedby') || ('td'+j);
                     info[aria] = tds[j].innerText.trim().slice(0,60);
                  }
                  return info;
               }
               return null;
            })())
        """)
        data = json.loads(res) if res else {}
        for k, v in data.items():
            if v:
                print(f"  {k:35} = {v!r}")

        return 0


if __name__ == "__main__":
    sys.exit(main())
