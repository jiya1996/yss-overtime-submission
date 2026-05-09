"""Debug: 列表页 → 创建▾ → 多条创建，dump 网格结构"""
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
            page.wait_for_load_state("networkidle", timeout=12000)
        except Exception:
            pass
        page.wait_for_timeout(1500)

        print(f"List URL: {page.url}")

        # 1. 找「创建」下拉按钮
        print("\n=== 找「创建」按钮 + 同 group 子项 ===")
        try:
            res = page.evaluate("""
                JSON.stringify((function(){
                   var groups = document.querySelectorAll('.btn-group');
                   var result = [];
                   for (var i = 0; i < groups.length; i++) {
                      var g = groups[i];
                      if (!g.innerText || g.innerText.indexOf('创建') === -1) continue;
                      result.push({
                         idx: i, cls: g.className,
                         html: g.outerHTML.slice(0, 1200)
                      });
                   }
                   return result;
                })())
            """)
            data = json.loads(res) if res else []
            for d in data:
                print(f"  group[{d['idx']}] cls={d['cls']!r}")
                print(f"  html:")
                print(d['html'])
                print()
        except Exception as e:
            print(f"失败: {e}")

        # 2. 点击「创建」下拉箭头展开（btn-group 通常有个 dropdown-toggle）
        print("\n=== 展开「创建」下拉 ===")
        try:
            # 先找一个「创建」附近的 dropdown-toggle，没有就直接点「创建」
            page.evaluate("""
                (function(){
                   var btns = document.querySelectorAll('button, a, span');
                   for (var i = 0; i < btns.length; i++) {
                      var b = btns[i];
                      if (b.innerText && b.innerText.trim() === '创建' && b.offsetParent !== null) {
                         // 模拟点击展开
                         var p = b.parentElement;
                         var toggle = p ? p.querySelector('.dropdown-toggle, .caret') : null;
                         if (toggle) {
                            toggle.click();
                         } else {
                            b.click();
                         }
                         return 'clicked: ' + b.tagName;
                      }
                   }
                   return null;
                })()
            """)
            page.wait_for_timeout(800)
            print("  ✅ 触发了创建按钮的点击")
        except Exception as e:
            print(f"  ⚠️  失败：{e}")

        # 3. dump 当前可见的「单条创建」「多条创建」等候选项
        print("\n=== 找「多条创建」选项 ===")
        try:
            res = page.evaluate("""
                JSON.stringify((function(){
                   var nodes = document.querySelectorAll('a, li, span, div, button');
                   var result = [];
                   for (var i = 0; i < nodes.length; i++) {
                      var n = nodes[i];
                      if (!n.innerText) continue;
                      var t = n.innerText.trim();
                      if (t === '多条创建' || t === '单条创建') {
                         result.push({
                            tag: n.tagName, text: t, id: n.id,
                            cls: (n.className||'').slice(0,60),
                            visible: n.offsetParent !== null,
                            onclick: (n.getAttribute('onclick')||'').slice(0,100)
                         });
                      }
                   }
                   return result;
                })())
            """)
            data = json.loads(res) if res else []
            for d in data:
                print(f"  {d}")
        except Exception as e:
            print(f"失败: {e}")

        # 4. 点击「多条创建」
        print("\n=== 点「多条创建」 ===")
        try:
            page.evaluate("""
                (function(){
                   var nodes = document.querySelectorAll('a, li, span, div, button');
                   for (var i = 0; i < nodes.length; i++) {
                      var n = nodes[i];
                      if (n.innerText && n.innerText.trim() === '多条创建') {
                         n.click();
                         return true;
                      }
                   }
                   return false;
                })()
            """)
            print("  ✅ 触发点击")
        except Exception as e:
            print(f"  ⚠️  失败：{e}")

        page.wait_for_timeout(2500)
        try:
            page.wait_for_load_state("networkidle", timeout=12000)
        except Exception:
            pass
        page.wait_for_timeout(1500)

        print(f"\n现在 URL：{page.url}")
        sp = screenshot_path("shr_multi_create.png")
        page.screenshot(path=sp, full_page=True)
        print(f"📸 截图：{sp}")

        # 5. dump 多条创建网格的列结构 + 第一行的 input/td selector
        print("\n=== 网格表头 ===")
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
                         hdrs.push({
                            idx: i,
                            text: ths[i].innerText.trim().slice(0, 30),
                            id: ths[i].id
                         });
                      }
                      result.push({tableIdx: ti, hdrs: hdrs, cls: tables[ti].className});
                   }
                   return result;
                })())
            """)
            data = json.loads(res) if res else []
            for r in data:
                print(f"  table[{r['tableIdx']}] cls={r['cls']!r}")
                for h in r['hdrs']:
                    if h['text']:
                        print(f"    th[{h['idx']:2}] text={h['text']!r}  id={h['id']!r}")
                print()
        except Exception as e:
            print(f"失败: {e}")

        # 6. 找「新增」按钮
        print("\n=== 找「新增」按钮 ===")
        try:
            res = page.evaluate("""
                JSON.stringify((function(){
                   var result = [];
                   var nodes = document.querySelectorAll('button, a, span');
                   for (var i = 0; i < nodes.length; i++) {
                      var n = nodes[i];
                      if (n.innerText && n.innerText.trim() === '新增' && n.offsetParent !== null) {
                         result.push({tag: n.tagName, id: n.id, cls: (n.className||'').slice(0,80)});
                      }
                   }
                   return result;
                })())
            """)
            data = json.loads(res) if res else []
            for d in data:
                print(f"  {d}")
        except Exception as e:
            print(f"失败: {e}")

        # 7. 看是否已经有一行待填，dump 行内 td/input
        print("\n=== 当前网格的行（td 内 input/select 的属性）===")
        try:
            res = page.evaluate("""
                JSON.stringify((function(){
                   var result = [];
                   // 找网格行：tr 里有多个 td 且有 input
                   var trs = document.querySelectorAll('tr');
                   for (var i = 0; i < trs.length && result.length < 3; i++) {
                      var tds = trs[i].querySelectorAll('td');
                      if (tds.length < 5) continue;
                      var hasInput = trs[i].querySelector('input, select, textarea');
                      if (!hasInput) continue;
                      var cells = [];
                      for (var j = 0; j < tds.length; j++) {
                         var td = tds[j];
                         var info = {idx: j, tdcls: (td.className||'').slice(0,50),
                                     dataField: td.getAttribute('data-field')||''};
                         var inp = td.querySelector('input, select, textarea');
                         if (inp) {
                            info.inp = {tag: inp.tagName, name: inp.name, id: inp.id,
                                        type: inp.type||'', placeholder: inp.placeholder||'',
                                        cls: (inp.className||'').slice(0,50),
                                        val: (inp.value||'').slice(0,30)};
                         }
                         info.text = td.innerText.trim().slice(0, 40);
                         cells.push(info);
                      }
                      result.push({rowIdx: i, cls: trs[i].className, cells: cells});
                   }
                   return result;
                })())
            """)
            data = json.loads(res) if res else []
            for r in data:
                print(f"  row[{r['rowIdx']}] cls={r['cls']!r}")
                for c in r['cells']:
                    print(f"    td[{c['idx']:2}] cls={c['tdcls']!r} data-field={c['dataField']!r}")
                    if 'inp' in c:
                        print(f"        inp = {c['inp']}")
                    if c.get('text'):
                        print(f"        text = {c['text']!r}")
                print()
        except Exception as e:
            print(f"失败: {e}")

        return 0


if __name__ == "__main__":
    sys.exit(main())
