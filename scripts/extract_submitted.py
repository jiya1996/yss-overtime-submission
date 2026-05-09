"""
从 SHR 拉已提交的奋斗单（用于差集判重）
========================================

实测路径（2026-05-08 跑通）：
  goto SHR_BILL_LIST_URL → 点「展开筛选」→ 填日期 → 点 #filter-search → 抓 tr.jqgrow

⚠️ 直接 goto BILL_FORM_URL 会被金蝶降级渲染成空白表单，必须用 BillList URL。
"""

from __future__ import annotations

import json
import re
from datetime import date as Date, datetime
from typing import Set, Dict, Any, List

from connect_chrome import find_or_open_tab, get_browser_context
from selectors import (
    SHR_BILL_LIST_URL,
    SHR_URL_PREFIX,
    SHR_BTN_EXPAND_FILTER_TEXT,
    SHR_FILTER_DATE_FROM_SEL,
    SHR_FILTER_DATE_TO_SEL,
    SHR_FILTER_QUERY_BTN_SEL,
    SHR_LIST_ROW_SEL,
    SHR_LIST_FIRSTROW_CLS,
    SHR_LIST_COL_BILL_NO_IDX,
    SHR_LIST_COL_DATE_IDX,
    SHR_LIST_COL_HOURS_IDX,
    SHR_LIST_COL_USAGE_IDX,
    SHR_LIST_COL_OT_TYPE_IDX,
    SHR_LIST_COL_STATUS_IDX,
    SHR_STATUS_VALID,
)


def fetch_submitted_records(start: Date, end: Date,
                            verbose: bool = True) -> List[Dict[str, Any]]:
    """抓 [start, end] 范围内的奋斗单，返回完整记录列表。

    每条记录形如：
      {bill_no, date, hours, usage, ot_type, status}

    与 fetch_submitted_dates 的区别：这个返回完整信息，那个只返回去重后的日期集合。
    """
    if verbose:
        print(f"📡 SHR 列表查询：{start} ~ {end}")

    records: List[Dict[str, Any]] = []

    with get_browser_context() as ctx:
        page = find_or_open_tab(ctx, SHR_URL_PREFIX, SHR_BILL_LIST_URL)
        page.goto(SHR_BILL_LIST_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        try:
            page.wait_for_load_state("networkidle", timeout=12000)
        except Exception:
            pass
        page.wait_for_timeout(1000)

        # 1. 展开筛选（如果折叠的话）
        try:
            page.get_by_text(SHR_BTN_EXPAND_FILTER_TEXT, exact=True).first.click(timeout=2500)
            page.wait_for_timeout(600)
        except Exception:
            pass  # 可能已展开

        # 2. 设置日期范围
        try:
            page.locator(SHR_FILTER_DATE_FROM_SEL).fill(start.isoformat())
            page.locator(SHR_FILTER_DATE_TO_SEL).fill(end.isoformat())
            page.wait_for_timeout(300)
        except Exception as e:
            if verbose:
                print(f"  ⚠️ 填日期失败：{e}")
            return records

        # 3. 点查询
        try:
            page.locator(SHR_FILTER_QUERY_BTN_SEL).click(timeout=5000)
        except Exception as e:
            if verbose:
                print(f"  ❌ 查询点击失败：{e}")
            return records

        page.wait_for_timeout(2500)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        page.wait_for_timeout(800)

        # 4. 抓 jqGrid 数据行（用 evaluate 一次性拉，避免 Playwright locator 在 jqGrid 上的兼容问题）
        js = f"""
            JSON.stringify((function(){{
               var result = [];
               var rows = document.querySelectorAll('{SHR_LIST_ROW_SEL}');
               for (var i = 0; i < rows.length; i++) {{
                  var tr = rows[i];
                  if ((tr.className||'').indexOf('{SHR_LIST_FIRSTROW_CLS}') >= 0) continue;
                  var tds = tr.querySelectorAll('td');
                  if (tds.length <= {SHR_LIST_COL_STATUS_IDX}) continue;
                  function txt(idx) {{ return tds[idx] ? tds[idx].innerText.trim() : ''; }}
                  result.push({{
                     bill_no: txt({SHR_LIST_COL_BILL_NO_IDX}),
                     date:    txt({SHR_LIST_COL_DATE_IDX}),
                     hours:   txt({SHR_LIST_COL_HOURS_IDX}),
                     usage:   txt({SHR_LIST_COL_USAGE_IDX}),
                     ot_type: txt({SHR_LIST_COL_OT_TYPE_IDX}),
                     status:  txt({SHR_LIST_COL_STATUS_IDX})
                  }});
               }}
               return result;
            }})())
        """
        try:
            raw = page.evaluate(js)
            data = json.loads(raw) if raw else []
        except Exception as e:
            if verbose:
                print(f"  ⚠️ 抓表格失败：{e}")
            return records

        for rec in data:
            if not re.match(r"\d{4}-\d{2}-\d{2}", rec.get('date', '')):
                continue
            records.append(rec)

        if verbose:
            print(f"✅ 抓到 {len(records)} 条单据：")
            for r in records:
                tag = "✓" if r['status'] in SHR_STATUS_VALID else "✗"
                print(f"    {tag} {r['date']} {r['hours']}h {r['usage']} - {r['status']} ({r['bill_no']})")

    return records


def fetch_submitted_dates(start: Date, end: Date,
                          verbose: bool = True) -> Set[Date]:
    """只返回有效已提交奋斗单的日期集合（差集判重用）。

    "有效" = 单据状态在 SHR_STATUS_VALID 里（审批中/审批通过/待审批）。
    被驳回 / 已撤回的不算"已提交" → 这些日期可以重新提交。
    """
    records = fetch_submitted_records(start, end, verbose=verbose)
    submitted: Set[Date] = set()
    for r in records:
        if r['status'] not in SHR_STATUS_VALID:
            continue
        try:
            d = datetime.strptime(r['date'][:10], "%Y-%m-%d").date()
            if start <= d <= end:
                submitted.add(d)
        except ValueError:
            continue

    if verbose:
        print(f"✅ 有效已提交日期 {len(submitted)} 个："
              + ", ".join(str(d) for d in sorted(submitted)))
    return submitted


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    parser.add_argument("--full", action="store_true",
                        help="打印完整记录而非仅日期集合")
    args = parser.parse_args()

    s = datetime.strptime(args.start, "%Y-%m-%d").date()
    e = datetime.strptime(args.end, "%Y-%m-%d").date()

    if args.full:
        fetch_submitted_records(s, e)
    else:
        fetch_submitted_dates(s, e)
