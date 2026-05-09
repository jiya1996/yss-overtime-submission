"""
从禅道工时确认页拉某日维护的项目+任务名+描述，作为奋斗内容的候选。
================================================================

真实 URL pattern（host 在 selectors.py 配置）：
  https://{ZENTAO_HOST}/index.php?m=todo&f=confirmuserconsumed&day=YYYY-MM-DD

表格列序（验证过）：
  0=ID 1=类型 2=编号 3=名称 4=状态 5=起止时间 6=时间暂定
  7=工时 8=项目(维护说明) 9=客户 10=对应系统 11=任务类型 12=描述

⚠️ 关键坑：「名称」「工时」「描述」三列是 <input value="..."> 不是文本，
   必须用 td.querySelector('input').value 才能拿到真值。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date as Date
from typing import List

from connect_chrome import find_or_open_tab, get_browser_context
from selectors import (
    ZT_EFFORT_URL,
    ZENTAO_URL_PREFIX,
    ZT_EFFORT_COL_NAME_IDX,
    ZT_EFFORT_COL_HOURS_IDX,
    ZT_EFFORT_COL_PROJECT_IDX,
    ZT_EFFORT_COL_DESC_IDX,
    ZT_EFFORT_COL_TASK_TYPE_IDX,
)


@dataclass
class EffortItem:
    """禅道工时确认页的一条记录里我们关心的字段。"""
    name: str = ""           # 任务名称（最适合作为奋斗内容）
    hours: float = 0.0       # 当天工时
    project: str = ""        # 项目（维护说明）
    description: str = ""    # 任务描述
    task_type: str = ""      # 任务类型，如「文档编写」「需求分析」

    def to_summary(self, prefer: str = "name") -> str:
        """生成一段简短的奋斗内容片段。

        prefer:
          'name' - 用任务名称（推荐）
          'desc' - 用描述
          'both' - 名称 + 描述
        """
        bits = []
        if prefer in ("name", "both") and self.name:
            bits.append(self.name)
        if prefer in ("desc", "both") and self.description:
            bits.append(self.description)
        if not bits and self.project:
            bits.append(self.project)
        return "、".join(bits)


def fetch_efforts(target_date: Date, verbose: bool = True) -> List[EffortItem]:
    """拉取指定日期在禅道工时确认页维护的工作项目（仅工时 > 0 的）。"""
    url = ZT_EFFORT_URL.format(date=target_date.isoformat())

    if verbose:
        print(f"📡 拉取 {target_date} 的禅道工时确认...")
        print(f"   URL: {url}")

    items: List[EffortItem] = []

    with get_browser_context() as ctx:
        page = find_or_open_tab(ctx, ZENTAO_URL_PREFIX, url)
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        page.wait_for_timeout(800)

        # 用 evaluate 一次性提取（避开 Playwright locator 处理 input 的开销）
        # 关键：拿 input.value 而不是 td.innerText
        js = f"""
            JSON.stringify((function(){{
               var result = [];
               var trs = document.querySelectorAll('table.table-1 tbody tr, table.colored tbody tr');
               for (var i = 0; i < trs.length; i++) {{
                  var tds = trs[i].querySelectorAll('td');
                  if (tds.length < 13) continue;
                  function val(td) {{
                     var ip = td.querySelector('input[type="text"], textarea');
                     if (ip) return (ip.value || '').trim();
                     var sel = td.querySelector('select');
                     if (sel && sel.options[sel.selectedIndex]) return sel.options[sel.selectedIndex].text.trim();
                     var t = td.innerText.trim();
                     return t.split('\\n').map(function(s){{return s.trim();}}).filter(Boolean)[0] || '';
                  }}
                  var rec = {{
                     name: val(tds[{ZT_EFFORT_COL_NAME_IDX}]),
                     hours: parseFloat(val(tds[{ZT_EFFORT_COL_HOURS_IDX}])) || 0,
                     project: val(tds[{ZT_EFFORT_COL_PROJECT_IDX}]),
                     desc: val(tds[{ZT_EFFORT_COL_DESC_IDX}]),
                     task_type: val(tds[{ZT_EFFORT_COL_TASK_TYPE_IDX}])
                  }};
                  // 仅保留实际有工时的（>0）
                  if (rec.hours > 0 || rec.name) {{
                     result.push(rec);
                  }}
               }}
               return result;
            }})())
        """
        try:
            res = page.evaluate(js)
            data = json.loads(res) if res else []
        except Exception as e:
            if verbose:
                print(f"  ⚠️  evaluate 失败：{e}")
            return items

        for rec in data:
            if rec.get('hours', 0) <= 0 and not rec.get('name'):
                continue
            items.append(EffortItem(
                name=rec.get('name', ''),
                hours=float(rec.get('hours', 0)),
                project=rec.get('project', ''),
                description=rec.get('desc', ''),
                task_type=rec.get('task_type', ''),
            ))

        if verbose:
            print(f"✅ 抓到 {len(items)} 条工时记录（工时>0）")
            for it in items:
                print(f"    • {it.name} ({it.hours}h) — {it.project}"
                      + (f" — {it.description}" if it.description else ""))

    return items


def merge_efforts_to_content(items: List[EffortItem],
                             max_items: int = 4,
                             prefer: str = "name") -> str:
    """把多条工时项目合并成一句奋斗内容文本。

    >>> # 中性测试数据（任务A 工时多排前面）
    >>> items = [
    ...     EffortItem(name='任务A', hours=3.5, project='项目X', description='测试描述'),
    ...     EffortItem(name='任务B', hours=2.0, project='项目Y'),
    ... ]
    >>> merge_efforts_to_content(items)
    '任务A、任务B'
    >>> merge_efforts_to_content([])
    ''
    """
    bits = []
    # 按工时降序，挑大头
    sorted_items = sorted(items, key=lambda x: x.hours, reverse=True)
    for it in sorted_items[:max_items]:
        s = it.to_summary(prefer=prefer)
        if s and s not in bits:
            bits.append(s)
    return "、".join(bits)


if __name__ == "__main__":
    import doctest
    failures, tests = doctest.testmod(verbose=False)
    if failures:
        raise SystemExit(f"❌ {failures}/{tests} doctest failed")

    import argparse
    from datetime import datetime
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--prefer", default="name", choices=["name", "desc", "both"])
    args = parser.parse_args()
    d = datetime.strptime(args.date, "%Y-%m-%d").date()
    items = fetch_efforts(d)
    print()
    print("→ 合并后的奋斗内容建议：")
    print(f"  {merge_efforts_to_content(items, prefer=args.prefer)}")
