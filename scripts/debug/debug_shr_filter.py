"""
Debug 第三步：在列表页展开筛选 → dump 日期 input + 查询按钮 selector
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

        print(f"List URL: {page.url}")

        # 1. 点「展开筛选」
        print("\n=== 点「展开筛选」 ===")
        try:
            loc = page.get_by_text("展开筛选", exact=True).first
            cnt = page.get_by_text("展开筛选", exact=True).count()
            print(f"  匹配数：{cnt}")
            if cnt > 0:
                try:
                    loc.click(timeout=3000)
                    print("  ✅ 普通点击")
                except Exception:
                    page.evaluate("""
                        var spans = document.querySelectorAll('span');
                        for (var i = 0; i < spans.length; i++) {
                            if (spans[i].innerText.trim() === '展开筛选') {
                                spans[i].click();
                                break;
                            }
                        }
                    """)
                    print("  ✅ JS click 触发")
            else:
                print("  ⚠️  未找到「展开筛选」，可能筛选区已展开或元素不同")
        except Exception as e:
            print(f"  ⚠️  失败：{e}")

        page.wait_for_timeout(1500)

        # 2. dump 当前所有可见 input
        print("\n=== 展开后所有可见 input ===")
        try:
            res = page.evaluate("""
                JSON.stringify(
                  Array.from(document.querySelectorAll('input'))
                    .filter(function(el){return el.offsetParent !== null;})
                    .slice(0, 50)
                    .map(function(el, idx){
                       return {idx: idx, type: el.type, name: el.name, id: el.id,
                               placeholder: el.placeholder, cls: (el.className||'').slice(0,60),
                               val: (el.value||'').slice(0,30),
                               readonly: el.readOnly};
                    })
                )
            """)
            data = json.loads(res) if res else []
            for inp in data:
                print(f"  {inp}")
        except Exception as e:
            print(f"  失败：{e}")

        # 3. dump 候选「查询」按钮
        print("\n=== 候选「查询」按钮 ===")
        try:
            res = page.evaluate("""
                JSON.stringify(
                  Array.from(document.querySelectorAll('button, a, span, div'))
                    .filter(function(el){return el.offsetParent !== null && el.innerText && el.innerText.trim() === '查询';})
                    .map(function(el){
                       return {tag: el.tagName, cls: (el.className||'').slice(0,80),
                               id: el.id, onclick: (el.getAttribute('onclick')||'').slice(0,60)};
                    })
                )
            """)
            data = json.loads(res) if res else []
            for b in data:
                print(f"  {b}")
        except Exception as e:
            print(f"  失败：{e}")

        # 4. 看「奋斗日期」标签所在的 DOM 区域
        print("\n=== 「奋斗日期」标签附近的结构 ===")
        try:
            res = page.evaluate("""
                JSON.stringify((function(){
                   var nodes = document.querySelectorAll('span, label, div');
                   for (var i = 0; i < nodes.length; i++) {
                      var n = nodes[i];
                      if (n.innerText && n.innerText.trim() === '奋斗日期' && n.offsetParent !== null) {
                         var parent = n.parentElement;
                         var grand = parent ? parent.parentElement : null;
                         return {
                             tag: n.tagName, cls: n.className,
                             parent_tag: parent ? parent.tagName : null,
                             parent_cls: parent ? parent.className : null,
                             grand_html: grand ? grand.outerHTML.slice(0, 1500) : null
                         };
                      }
                   }
                   return null;
                })())
            """)
            data = json.loads(res) if res else None
            if data:
                print(f"  标签 tag={data['tag']} cls={data['cls']}")
                print(f"  parent: tag={data['parent_tag']} cls={data['parent_cls']}")
                print(f"  grandparent HTML (前 1500 字)：")
                print(data['grand_html'])
            else:
                print("  没找到「奋斗日期」标签")
        except Exception as e:
            print(f"  失败：{e}")

        # 5. 截图
        sp = screenshot_path("shr_filter.png")
        page.screenshot(path=sp, full_page=True)
        print(f"\n📸 截图：{sp}")

        return 0


if __name__ == "__main__":
    sys.exit(main())
