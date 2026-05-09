"""
半自动提交 5/6 加班单：填好所有字段，停在「提交」按钮前等用户确认。
=========================================================================
"""
from __future__ import annotations
import json
import sys
import time
from _debug_utils import screenshot_path
from connect_chrome import find_or_open_tab, get_browser_context

MULTI_CREATE_URL = (
    "https://oa.example.com:5887/shr/dynamic.do"
    "?uipk=com.kingdee.eas.hr.ats.app.AtsOverTimeBillForm.PersonnalBatch"
    "&inFrame=true&billId=&method=addNew"
)

TARGET_DATE = "2026-05-06"
TARGET_POINTS = "1.5"
TARGET_USAGE = "奋斗积分"  # 工作日只能选这个
TARGET_DESC = "<your work content>"


def dump_row(page):
    """dump 当前网格里第一个数据行的 cell + input 信息"""
    res = page.evaluate("""
        JSON.stringify((function(){
           var trs = document.querySelectorAll('tr');
           for (var i = 0; i < trs.length; i++) {
              var tr = trs[i];
              var tds = tr.querySelectorAll('td');
              if (tds.length < 5) continue;
              var hasInput = tr.querySelector('input, select, textarea');
              if (!hasInput) continue;
              // 跳过表头
              if (tr.querySelector('th')) continue;
              if ((tr.className||'').indexOf('jqgfirstrow') >= 0) continue;

              var cells = [];
              for (var j = 0; j < tds.length; j++) {
                 var td = tds[j];
                 var info = {idx: j,
                             tdcls: (td.className||'').slice(0,40),
                             aria: td.getAttribute('aria-describedby')||'',
                             attrs: {}};
                 var inp = td.querySelector('input, select, textarea');
                 if (inp) {
                    info.inp = {tag: inp.tagName, name: inp.name, id: inp.id,
                                type: inp.type||'', cls: (inp.className||'').slice(0,40),
                                val: (inp.value||'').slice(0,40),
                                readonly: inp.readOnly||false};
                 }
                 info.text = td.innerText.trim().slice(0, 50);
                 cells.push(info);
              }
              return {rowIdx: i, cls: tr.className, id: tr.id, cells: cells};
           }
           return null;
        })())
    """)
    return json.loads(res) if res else None


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

        print(f"URL: {page.url}")
        print(f"Title: {page.title()}")

        # 1. 点「新增」
        print("\n=== Step 1: 点「新增」加一行 ===")
        try:
            page.locator("#addRow_entries").click(timeout=5000)
            print("  ✅ 已点击新增")
        except Exception as e:
            print(f"  ⚠️ 普通 click 失败：{e}")
            try:
                page.evaluate("document.getElementById('addRow_entries').click()")
                print("  ✅ JS click 成功")
            except Exception as e2:
                print(f"  ❌ JS click 也失败：{e2}")
                return 1

        page.wait_for_timeout(1500)

        # 2. dump 新行结构
        print("\n=== Step 2: dump 新行 cell 结构 ===")
        row = dump_row(page)
        if not row:
            print("  ❌ 没找到数据行，停下")
            page.screenshot(path=screenshot_path("shr_after_addrow.png"), full_page=True)
            return 1

        print(f"  rowIdx={row['rowIdx']}  cls={row['cls']!r}  id={row['id']!r}")
        for c in row['cells']:
            line = f"    td[{c['idx']:2}] aria={c['aria']!r:30} text={c['text']!r}"
            if 'inp' in c:
                line += f"\n        inp = {c['inp']}"
            print(line)

        # 3. 基于 aria-describedby 用列 id 找单元格 → 点击进入编辑 → 填值
        # 单元格的 aria-describedby = 列头的 id（如 entries_otDate）
        # 进入编辑模式：双击或者 click 触发 jqGrid inline edit
        print("\n=== Step 3: 填奋斗日期 ===")
        try:
            # 找该行里 aria-describedby='entries_otDate' 的 td
            # jqGrid 通常用 click 进入 edit mode，cell 内 input 才能填
            # 先 click 该 cell 进入 edit
            cell_sel = f'tr[id="{row["id"]}"] td[aria-describedby="entries_otDate"]' if row.get('id') else 'td[aria-describedby="entries_otDate"]'
            page.locator(cell_sel).first.click(timeout=3000)
            page.wait_for_timeout(500)
            # cell 进入 edit 后会有 input
            cell_input = page.locator(f'{cell_sel} input').first
            try:
                cell_input.fill(TARGET_DATE)
                page.wait_for_timeout(300)
                # 触发 blur 或按 Tab 让金蝶接受值
                cell_input.press("Tab")
            except Exception:
                # 备选：直接在文档里找 entries_otDate 相关的 input
                pass
            page.wait_for_timeout(800)
            print("  ✅ 奋斗日期已尝试填")
        except Exception as e:
            print(f"  ⚠️ 失败：{e}")

        # 由于复杂的金蝶 cell editing 行为，先停下来截图给用户看效果
        page.wait_for_timeout(1000)
        sp = screenshot_path("shr_filled.png")
        page.screenshot(path=sp, full_page=True)
        print(f"\n📸 当前状态截图：{sp}")

        # 再 dump 一次行看现在变成什么样
        print("\n=== 再 dump 一次行（看填日期后的变化）===")
        row2 = dump_row(page)
        if row2:
            for c in row2['cells']:
                if c.get('text') or 'inp' in c:
                    line = f"    td[{c['idx']:2}] aria={c['aria']!r:30} text={c['text']!r}"
                    if 'inp' in c:
                        line += f"\n        inp = {c['inp']}"
                    print(line)

        return 0


if __name__ == "__main__":
    sys.exit(main())
