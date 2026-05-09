"""
从禅道抓打卡数据
==================

使用 Playwright 连接到已登录的 Chrome，访问禅道考勤页直接拉数据。
"""

from __future__ import annotations

import re
from datetime import date as Date, datetime
from typing import List

from calculator import AttendanceRecord
from connect_chrome import find_or_open_tab, get_browser_context
from holidays import is_workday as is_workday_cn
from selectors import (
    ZT_ATTENDANCE_URL,
    ZT_ATTENDANCE_ROW_SEL,
    ZT_COL_DATE_IDX,
    ZT_COL_WEEKDAY_IDX,
    ZT_COL_PUNCH_IDX,
    ZENTAO_URL_PREFIX,
)


def parse_punch_str(s: str) -> tuple[str, str]:
    """解析 '08:46,21:33' 这种打卡字段。

    >>> parse_punch_str("08:46,21:33")
    ('08:46', '21:33')
    >>> parse_punch_str("08:46")  # 只打了上班卡
    ('08:46', '')
    >>> parse_punch_str("")
    ('', '')
    """
    if not s.strip():
        return ("", "")
    parts = [p.strip() for p in s.split(",") if p.strip()]
    if len(parts) >= 2:
        return (parts[0], parts[1])
    elif len(parts) == 1:
        return (parts[0], "")
    return ("", "")


def fetch_attendance(start: Date, end: Date,
                     verbose: bool = True) -> List[AttendanceRecord]:
    """从禅道拉指定日期范围的打卡记录。

    Args:
        start: 开始日期
        end: 结束日期
        verbose: 是否打印调试信息

    Returns:
        AttendanceRecord 列表
    """
    url = ZT_ATTENDANCE_URL.format(start=start.isoformat(), end=end.isoformat())

    if verbose:
        print(f"📡 访问禅道考勤页：{url}")

    with get_browser_context() as ctx:
        page = find_or_open_tab(ctx, ZENTAO_URL_PREFIX, fallback_url=url)
        # 不管 tab 是不是已经在禅道，强制跳转到目标日期范围
        page.goto(url, wait_until="networkidle")

        # 等表格加载（用最朴素的 wait）
        page.wait_for_selector(ZT_ATTENDANCE_ROW_SEL, timeout=10000)

        rows = page.locator(ZT_ATTENDANCE_ROW_SEL)
        n = rows.count()

        if verbose:
            print(f"📊 表格找到 {n} 行")

        records: List[AttendanceRecord] = []
        for i in range(n):
            row = rows.nth(i)
            tds = row.locator("td")
            if tds.count() < 3:
                continue

            try:
                date_str = tds.nth(ZT_COL_DATE_IDX).inner_text().strip()
                weekday = tds.nth(ZT_COL_WEEKDAY_IDX).inner_text().strip()
                punch_str = tds.nth(ZT_COL_PUNCH_IDX).inner_text().strip()
            except Exception as e:
                if verbose:
                    print(f"  ⚠️  第 {i} 行解析失败：{e}")
                continue

            # 验证日期格式
            if not re.match(r"\d{4}-\d{2}-\d{2}", date_str):
                continue

            clock_in, clock_out = parse_punch_str(punch_str)
            d = datetime.strptime(date_str, "%Y-%m-%d").date()

            records.append(AttendanceRecord(
                date=d,
                weekday=weekday,
                clock_in=clock_in,
                clock_out=clock_out,
                is_workday=is_workday_cn(d),  # 用中国大陆节假日库判断
            ))

        if verbose:
            print(f"✅ 抓到 {len(records)} 条有效记录")

    return records


if __name__ == "__main__":
    import doctest
    doctest.testmod()

    # 命令行调试用
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    args = parser.parse_args()

    s = datetime.strptime(args.start, "%Y-%m-%d").date()
    e = datetime.strptime(args.end, "%Y-%m-%d").date()

    records = fetch_attendance(s, e)
    print()
    print(f"{'日期':<12} {'星期':<4} {'上班':<6} {'下班':<6} 工作日")
    print("-" * 40)
    for r in records:
        print(f"{r.date}  {r.weekday}  {r.clock_in:<6} {r.clock_out:<6} {r.is_workday}")
