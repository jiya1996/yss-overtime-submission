"""拉 5/6 当天的禅道工时确认数据。"""
from __future__ import annotations
import json
import sys
from _debug_utils import screenshot_path
from connect_chrome import find_or_open_tab, get_browser_context

URL = "https://pm.example.com:8071/index.php?m=todo&f=confirmuserconsumed&day=YYYY-MM-DD"


def main():
    with get_browser_context() as ctx:
        page = find_or_open_tab(ctx, "https://pm.example.com", URL)
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        page.wait_for_timeout(800)

        # 确认日期
        try:
            day_val = page.evaluate("document.getElementById('day') ? document.getElementById('day').value : null")
            print(f"页面日期：{day_val}")
        except Exception:
            pass

        # 抓所有数据行（带 input 的）
        print("\n=== 5/6 工时确认数据行 ===")
        try:
            res = page.evaluate("""
                JSON.stringify((function(){
                   var result = [];
                   var trs = document.querySelectorAll('table.table-1 tbody tr, table.colored tbody tr');
                   for (var i = 0; i < trs.length; i++) {
                      var tds = trs[i].querySelectorAll('td');
                      if (tds.length < 8) continue;
                      var rec = {};
                      // 列序：0=ID 1=类型 2=编号 3=名称 4=状态 5=起止时间 6=时间暂定 7=工时 8=项目 9=客户 10=对应系统 11=任务类型 12=描述
                      function getInputVal(td){
                         var ip = td.querySelector('input[type="text"], textarea');
                         return ip ? (ip.value||'').trim() : '';
                      }
                      function pureText(td){
                         var t = td.innerText.trim();
                         // 如果是 select 列表（status/任务类型 等），找 selected
                         var sel = td.querySelector('select');
                         if (sel) return sel.options[sel.selectedIndex] ? sel.options[sel.selectedIndex].text : '';
                         return t.split('\\n').map(function(s){return s.trim();}).filter(Boolean)[0] || '';
                      }
                      rec.id = pureText(tds[0]);
                      rec.type = pureText(tds[1]);
                      rec.code = pureText(tds[2]);
                      rec.name = getInputVal(tds[3]) || pureText(tds[3]);
                      rec.status = pureText(tds[4]);
                      rec.hours = getInputVal(tds[7]) || pureText(tds[7]);
                      rec.project = pureText(tds[8]);
                      rec.system = pureText(tds[10]);
                      rec.task_type = pureText(tds[11]);
                      rec.desc = getInputVal(tds[12]) || pureText(tds[12]);
                      // 只要工时 > 0 或者名称非空才算数据行
                      if (rec.hours || rec.name || rec.id) {
                         result.push(rec);
                      }
                   }
                   return result;
                })())
            """)
            data = json.loads(res) if res else []
            print(f"  共 {len(data)} 行：")
            for i, r in enumerate(data):
                print(f"\n  ━━ row {i} ━━")
                print(f"    ID:        {r.get('id')!r}")
                print(f"    类型:      {r.get('type')!r}")
                print(f"    编号:      {r.get('code')!r}")
                print(f"    名称:      {r.get('name')!r}")
                print(f"    状态:      {r.get('status')!r}")
                print(f"    工时:      {r.get('hours')!r}")
                print(f"    项目:      {r.get('project')!r}")
                print(f"    对应系统:  {r.get('system')!r}")
                print(f"    任务类型:  {r.get('task_type')!r}")
                print(f"    描述:      {r.get('desc')!r}")
        except Exception as e:
            print(f"失败：{e}")

        sp = screenshot_path("zt_effort_5_6.png")
        page.screenshot(path=sp, full_page=True)
        print(f"\n📸 截图：{sp}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
