"""
模拟跑（不连浏览器）
=====================

用预设的"模拟禅道打卡 + 模拟 SHR 已提交清单"跑一遍完整逻辑，
验证：
  1. 中国节假日识别（含调休补班）
  2. 工作日 / 非工作日规则切换
  3. 时长计算（取整、扣餐）
  4. 差集判重
  5. 输出格式

运行：
    python simulate.py
    python simulate.py --start 2025-09-29 --end 2025-10-08  # 国庆节那周
"""

from __future__ import annotations

import argparse
from datetime import date as Date, timedelta
from typing import Dict, Tuple

from calculator import (
    AttendanceRecord,
    OvertimeBill,
    compute_bill,
    diff_against_submitted,
    split_overtime_bill,
)
from holidays import is_workday, get_day_label


# ===========================================================
# 预设的模拟打卡数据（key=日期, value=(上班, 下班) 或 None=没打卡）
# ===========================================================

MOCK_ATTENDANCE: Dict[Date, Tuple[str, str]] = {
    # 你 workflow 文档里的真实例子
    Date(2026, 4, 18): ("11:48", "20:50"),  # 周六加班
    Date(2026, 4, 19): ("12:02", "18:19"),  # 周日加班
    Date(2026, 4, 20): ("08:46", "21:33"),  # 周一加班
    Date(2026, 4, 21): ("08:44", "18:46"),  # 周二正常
    Date(2026, 4, 22): ("08:49", "21:10"),  # 周三加班
    Date(2026, 4, 23): ("08:45", "22:07"),  # 周四加班
    Date(2026, 5, 10): ("09:44", "22:58"),  # 周日长加班，净 11h，需要拆分

    # === 国庆节那周（2025-09-29 ~ 2025-10-08）===
    # 包含：国庆假期 + 假期前调休补班的周日 + 假期后正常上班
    Date(2025, 9, 28): ("08:50", "21:00"),  # 周日：国庆调休补班
    Date(2025, 9, 29): ("08:45", "20:30"),  # 周一：节前正常工作日
    Date(2025, 9, 30): ("08:30", "19:30"),  # 周二：节前正常工作日
    Date(2025, 10, 1): ("10:00", "20:00"),  # 国庆，加班
    Date(2025, 10, 2): ("11:30", "18:30"),  # 国庆，加班
    Date(2025, 10, 3): None,                # 国庆，没打卡
    Date(2025, 10, 4): None,                # 国庆，没打卡
    Date(2025, 10, 5): None,                # 国庆，没打卡
    Date(2025, 10, 6): None,                # 国庆中秋假期，没打卡
    Date(2025, 10, 7): None,                # 国庆，没打卡
    Date(2025, 10, 8): ("08:48", "21:00"),  # 周三，节后第一天加班

    # === 春节调休补班测试（2025-01-26 周日是补班）===
    Date(2025, 1, 26): ("08:55", "20:00"),  # 周日补班，按工作日加班规则！
}

# 模拟 SHR 已提交的日期集合（用来测差集）
MOCK_SUBMITTED = {
    Date(2026, 4, 20),   # 4-20 周一已经提过了
    Date(2025, 9, 29),   # 9-29 节前已经提过了
    Date(2025, 10, 8),   # 10-8 节后已经提过了
}


def simulate(start: Date, end: Date, prefer_compensation: bool = True) -> None:
    """跑一遍模拟流程并打印每一步。"""

    print("=" * 78)
    print(f"📅 模拟日期范围：{start} ~ {end}")
    print(f"   非工作日默认使用方式：{'调休' if prefer_compensation else '奋斗积分'}")
    print("=" * 78)

    # -------- 阶段 1：构造打卡记录（模拟从禅道抓数据）--------
    print("\n【阶段 1】「禅道」考勤数据（模拟）")
    print("-" * 78)
    print(f"{'日期':<12}{'类型标注':<28}{'打卡':<18}{'类型':<10}")
    print("-" * 78)

    records = []
    cur = start
    while cur <= end:
        weekday_name = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][cur.weekday()]
        label = get_day_label(cur)

        if cur in MOCK_ATTENDANCE and MOCK_ATTENDANCE[cur]:
            ci, co = MOCK_ATTENDANCE[cur]
            iw = is_workday(cur)
            records.append(AttendanceRecord(
                date=cur, weekday=weekday_name,
                clock_in=ci, clock_out=co, is_workday=iw,
            ))
            type_str = '工作日' if iw else '非工作日'
            print(f"{str(cur):<12}{label:<28}{ci+'~'+co:<18}{type_str:<10}")
        else:
            print(f"{str(cur):<12}{label:<28}{'(无打卡)':<18}")
        cur += timedelta(days=1)

    # -------- 阶段 2：模拟 SHR 已提交清单 --------
    print("\n【阶段 2】「SHR」已提交奋斗单（模拟）")
    print("-" * 78)
    submitted_in_range = {d for d in MOCK_SUBMITTED if start <= d <= end}
    if submitted_in_range:
        for d in sorted(submitted_in_range):
            print(f"  ✓ {d}（已提交，跳过）")
    else:
        print("  （范围内无已提交记录）")

    # -------- 阶段 3：算应提交清单 --------
    print("\n【阶段 3】按规则计算应提交清单")
    print("-" * 78)
    all_bills = []
    for r in records:
        bill = compute_bill(r, prefer_compensation=prefer_compensation)
        if bill:
            parts = split_overtime_bill(bill)
            all_bills.extend(parts)
            for part in parts:
                print(f"  ✓ {part.to_line()}")
        else:
            print(f"  ✗ {r.date} {r.weekday} 不需提交（时长不够 / 当天未加班）")

    # -------- 阶段 4：差集 --------
    print("\n【阶段 4】差集（应提交 − 已提交 = 待提交）")
    print("-" * 78)
    pending = diff_against_submitted(all_bills, submitted_in_range)
    if pending:
        for b in pending:
            print(f"  ★ {b.to_line()}")
    else:
        print("  （范围内不需要补提交任何加班单）")

    # -------- 总结 --------
    print()
    print("=" * 78)
    print(f"📊 总结：应提交 {len(all_bills)} 条，已提交 {len(submitted_in_range)} 条，"
          f"待提交 {len(pending)} 条")
    print("=" * 78)


def main():
    parser = argparse.ArgumentParser(description="加班单逻辑模拟器（不连浏览器）")
    parser.add_argument("--start", default="2026-04-18", help="YYYY-MM-DD")
    parser.add_argument("--end", default="2026-04-23", help="YYYY-MM-DD")
    parser.add_argument("--prefer-points", action="store_true",
                        help="非工作日默认用奋斗积分而非调休")
    args = parser.parse_args()

    from datetime import datetime as DT
    start = DT.strptime(args.start, "%Y-%m-%d").date()
    end = DT.strptime(args.end, "%Y-%m-%d").date()

    simulate(start, end, prefer_compensation=not args.prefer_points)


if __name__ == "__main__":
    main()
