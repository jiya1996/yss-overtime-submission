"""
加班单提交工作流总入口
========================

执行顺序：
  1. 抓禅道打卡数据
  2. 抓 SHR 已提交清单
  3. 计算待提交差集
  4. 让用户为每条单据填奋斗内容
  5. 给用户最终确认
  6. 调 submit_overtime 提交

用法：
  python orchestrator.py --start 2026-04-20 --end 2026-04-26
  python orchestrator.py --start 2026-04-20 --end 2026-04-26 --confirm  # 不再二次问
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date as Date, datetime
from pathlib import Path
from typing import List

from calculator import (
    AttendanceRecord,
    OvertimeBill,
    compute_bill,
    diff_against_submitted,
    split_long_overtime_bills,
)


def main():
    parser = argparse.ArgumentParser(description="赢时胜加班单半自动提交工具")
    parser.add_argument("--start", required=True, help="查询起始日期 YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="查询结束日期 YYYY-MM-DD")
    parser.add_argument("--confirm", action="store_true",
                        help="跳过二次确认，直接提交（仍需 dry-run 通过）")
    parser.add_argument("--dry-run-only", action="store_true",
                        help="只 dry-run 不提交（即使加了 --confirm）")
    parser.add_argument(
        "--prefer-points", action="store_true",
        help="非工作日默认用奋斗积分而非调休（默认调休）",
    )
    parser.add_argument("--plan-file", default="plan.json",
                        help="待提交清单中间产物路径")
    parser.add_argument("--content", default=None,
                        help="为所有待提交单子预填同一段奋斗内容（备注）。"
                             "Bash 调用 input() 拿不到 stdin 时用这个。"
                             "示例：--content '<你当天做的事>'")
    args = parser.parse_args()

    start = datetime.strptime(args.start, "%Y-%m-%d").date()
    end = datetime.strptime(args.end, "%Y-%m-%d").date()

    print(f"\n{'=' * 70}")
    print(f"📅 处理日期范围：{start} ~ {end}")
    print(f"   非工作日默认使用方式：{'奋斗积分' if args.prefer_points else '调休'}")
    print(f"{'=' * 70}\n")

    # =================================================
    # 阶段 1：抓禅道打卡
    # =================================================
    print("【阶段 1】抓禅道打卡数据")
    print("-" * 70)
    from extract_attendance import fetch_attendance
    records = fetch_attendance(start, end)

    if not records:
        print("❌ 没抓到任何打卡记录，终止")
        sys.exit(1)

    # =================================================
    # 阶段 2：抓 SHR 已提交清单
    # =================================================
    print("\n【阶段 2】抓 SHR 已提交奋斗单")
    print("-" * 70)
    from extract_submitted import fetch_submitted_dates
    submitted_dates = fetch_submitted_dates(start, end)

    # =================================================
    # 阶段 3：计算差集
    # =================================================
    print("\n【阶段 3】计算待提交差集")
    print("-" * 70)
    all_bills: List[OvertimeBill] = []
    for r in records:
        b = compute_bill(r, prefer_compensation=not args.prefer_points)
        if b:
            all_bills.append(b)
    all_bills = split_long_overtime_bills(all_bills)

    pending = diff_against_submitted(all_bills, submitted_dates)
    print(f"  应提交 {len(all_bills)} 条，已提交 {len(submitted_dates)} 个日期")
    print(f"  待提交 {len(pending)} 条：")
    for b in pending:
        print(f"    - {b.to_line()}")

    if not pending:
        print("\n🎉 当前范围内没有需要补提交的加班单。")
        return

    # =================================================
    # 阶段 4：交互式填奋斗内容（先尝试从禅道工时拉建议）
    # =================================================
    print("\n【阶段 4】填写奋斗内容（每条单据必须有）")
    print("-" * 70)
    from extract_effort import fetch_efforts, merge_efforts_to_content

    # 收集每条单子的奋斗内容
    # 优先级：--content 命令行参数 > 用户交互输入 > 禅道工时建议
    # 如果三者都拿不到 → 抛错（不再使用任何默认占位，避免提交成"占位"假数据）
    missing_content: List[OvertimeBill] = []

    for b in pending:
        print(f"\n  📅 {b.date} {b.weekday} 加班 {b.hours}h")

        # 1) 优先用 --content 命令行参数（一句覆盖所有）
        if args.content:
            b.content = args.content.strip()
            print(f"     ← 使用 --content 预填：{b.content}")
            continue

        # 2) 尝试从禅道工时确认页拉建议
        suggestion = ""
        try:
            efforts = fetch_efforts(b.date, verbose=False)
            suggestion = merge_efforts_to_content(efforts)
        except Exception as e:
            print(f"     (⚠️  禅道工时拉取失败：{type(e).__name__})")

        # 3) 询问用户（终端交互）。bash/IDE 调用没有 stdin 时会 EOFError
        content = ""
        if suggestion:
            print(f"     💡 禅道工时建议：{suggestion}")
            try:
                ans = input("     回车采用建议，或直接输入新内容：\n     > ").strip()
            except EOFError:
                ans = ""
            content = ans or suggestion
        else:
            print(f"     ⚠️  禅道工时当天无记录，需要你手填奋斗内容")
            try:
                content = input("     请输入奋斗内容（必填，金蝶不允许空备注）：\n     > ").strip()
            except EOFError:
                content = ""

        if not content:
            # 不再用任何默认占位 —— 直接收集到 missing 列表，最后统一报错
            missing_content.append(b)
            print(f"     ❌ 没拿到奋斗内容")
        else:
            b.content = content

    if missing_content:
        print()
        print("=" * 70)
        print(f"❌ 有 {len(missing_content)} 条单子还没填奋斗内容，无法继续：")
        for b in missing_content:
            print(f"   - {b.date} {b.weekday} {b.hours}h")
        print()
        print("解决办法（任选其一）：")
        print("  A. 在终端里直接跑（能交互输入）")
        print("  B. 加 --content '<你当天做的事>' 给所有单子统一填一段")
        print("  C. 先去禅道工时确认页把当天工时填好再重跑")
        print("=" * 70)
        sys.exit(2)

    # =================================================
    # 阶段 5：保存中间产物 + 最终确认
    # =================================================
    plan_path = Path(args.plan_file)
    plan_data = []
    for b in pending:
        plan_data.append({
            "date": b.date.isoformat(),
            "weekday": b.weekday,
            "clock_in": b.clock_in,
            "clock_out": b.clock_out,
            "hours": b.hours,
            "bill_type": b.bill_type,
            "usage": b.usage,
            "content": b.content,
            "submit_start": b.submit_start,
            "submit_end": b.submit_end,
            "rest_minutes": b.rest_minutes,
            "segment_index": b.segment_index,
            "segment_count": b.segment_count,
        })
    plan_path.write_text(json.dumps(plan_data, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    print(f"\n💾 待提交清单已保存到 {plan_path}")

    # =================================================
    # 阶段 6：dry-run + 提交
    # =================================================
    print("\n【阶段 6】提交")
    print("-" * 70)
    from submit_overtime import submit_bills

    # 先无条件 dry-run 一次让用户看
    submit_bills(pending, confirm=False)

    if args.dry_run_only:
        print("\n--dry-run-only 已设置，结束。")
        return

    if args.confirm:
        do_submit = True
    else:
        try:
            ans = input("\n以上是即将提交的内容。确认提交？输入 'yes' 继续：").strip()
        except EOFError:
            ans = ""
        do_submit = (ans.lower() == "yes")

    if not do_submit:
        print("已取消，未提交。中间产物保留在 plan.json 供下次使用。")
        return

    submit_bills(pending, confirm=True)


if __name__ == "__main__":
    main()
