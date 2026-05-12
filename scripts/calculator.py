"""
赢时胜加班时长计算引擎 (pure logic, no IO)
==============================================

这个模块**只**负责按规则算时长，不碰浏览器、不碰文件。
所有计算规则的来源是 ../references/calculation_rules.md，
那里是规则的唯一权威定义；这里只是它的代码实现。

直接运行本文件可触发所有 doctest：
    python calculator.py

使用示例:
    >>> calc_workday("21:33")
    2.5
    >>> calc_holiday("11:48", "20:50")
    7.0
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Optional


# ---------------------------------------------------------------
# 底层工具函数
# ---------------------------------------------------------------

def _parse_hhmm(s: str) -> time:
    """把 'HH:MM' 字符串解析成 time 对象。

    >>> _parse_hhmm("08:46")
    datetime.time(8, 46)
    >>> _parse_hhmm("21:33")
    datetime.time(21, 33)
    """
    h, m = s.strip().split(":")
    return time(int(h), int(m))


def _format_hhmm(t: time) -> str:
    """把 time 格式化成 'HH:MM'。"""
    return f"{t.hour:02d}:{t.minute:02d}"


def _add_hours(t: time, hours: float, extra_minutes: int = 0) -> time:
    """给同一天内的 time 加小时/分钟。当前 skill 不支持跨天。"""
    dt = datetime.combine(date.today(), t) + timedelta(hours=hours, minutes=extra_minutes)
    if dt.date() != date.today():
        raise ValueError("split overtime across midnight is not supported")
    return dt.time().replace(second=0, microsecond=0)


def _hours_between(start: time, end: time) -> float:
    """返回 end - start 的小时数（float）。不处理跨天。

    >>> _hours_between(time(19, 0), time(21, 30))
    2.5
    >>> round(_hours_between(time(11, 48), time(20, 50)), 4)
    9.0333
    """
    start_dt = datetime.combine(date.today(), start)
    end_dt = datetime.combine(date.today(), end)
    return (end_dt - start_dt).total_seconds() / 3600.0


def _floor_to_half(hours: float) -> float:
    """向下取整到 0.5 小时。

    >>> _floor_to_half(2.55)
    2.5
    >>> _floor_to_half(2.0)
    2.0
    >>> _floor_to_half(1.99)
    1.5
    >>> _floor_to_half(7.033)
    7.0
    """
    return math.floor(hours * 2) / 2


# ---------------------------------------------------------------
# 核心计算规则
# ---------------------------------------------------------------

# 加班起算点（工作日）
WORKDAY_OT_START = time(19, 0)
# 午餐时段
LUNCH_START = time(12, 0)
# 晚餐时段
DINNER_START = time(18, 0)
# 晚餐结束 = 加班起算点 = 19:00
DINNER_END = time(19, 0)
# 提交资格门槛：实际时长必须严格 > 此值
ELIGIBILITY_THRESHOLD_HOURS = 1.0


def calc_workday(clock_out: str) -> Optional[float]:
    """工作日加班时长。

    规则：从 19:00 起算到下班打卡，必须严格 > 1h，向下取整到 0.5h。

    Args:
        clock_out: 下班打卡时间，'HH:MM'

    Returns:
        可提交小时数，或 None（不满足提交条件）

    >>> calc_workday("21:33")
    2.5
    >>> calc_workday("21:10")
    2.0
    >>> calc_workday("22:07")
    3.0
    >>> calc_workday("18:46") is None
    True
    >>> calc_workday("19:30") is None
    True
    >>> calc_workday("20:00") is None  # 严格 >1h，1h 不行
    True
    >>> calc_workday("20:01")  # 1h1min → 1h
    1.0
    >>> calc_workday("20:30")  # 边界 1.5h
    1.5
    """
    end = _parse_hhmm(clock_out)
    raw = _hours_between(WORKDAY_OT_START, end)

    if raw <= ELIGIBILITY_THRESHOLD_HOURS:
        return None

    return _floor_to_half(raw)


def calc_holiday(clock_in: str, clock_out: str) -> Optional[float]:
    """非工作日加班时长。

    规则：
      总时长 = 下班 − 上班
      若上班打卡 < 12:00：扣 1h 午餐
      若上班打卡 < 18:00 且 下班打卡 ≥ 19:00：扣 1h 晚餐
        （即必须完整跨越晚餐时段才扣；只跨入或只跨出都不扣）
      必须 > 1h，向下取整到 0.5h

    >>> calc_holiday("11:48", "20:50")  # 扣午餐+扣晚餐
    7.0
    >>> calc_holiday("12:02", "18:19")  # 都不扣
    6.0
    >>> calc_holiday("13:30", "18:30")  # 都不扣
    5.0
    >>> calc_holiday("09:00", "19:00")  # 上班<12 + 下班=19，都扣
    8.0
    >>> calc_holiday("13:00", "18:00")  # 13:00 不<12:00，不扣
    5.0
    >>> calc_holiday("11:59", "12:30") is None  # 净时长 0.5h，不够
    True
    >>> calc_holiday("18:30", "22:00")  # 上班>=18:00，没赶上晚餐时段，不扣
    3.5
    """
    start = _parse_hhmm(clock_in)
    end = _parse_hhmm(clock_out)

    raw = _hours_between(start, end)

    # 午餐扣除：上班打卡严格 < 12:00
    if start < LUNCH_START:
        raw -= 1.0

    # 晚餐扣除：必须**完整**跨越 18:00-19:00 才扣
    #   即：上班 < 18:00 且 下班 ≥ 19:00
    #   如果上班 >= 18:00 ，说明开始工作时晚餐时段已开始或已过，
    #   员工没机会吃晚餐 → 不扣
    if start < DINNER_START and end >= DINNER_END:
        raw -= 1.0

    if raw <= ELIGIBILITY_THRESHOLD_HOURS:
        return None

    return _floor_to_half(raw)


# ---------------------------------------------------------------
# 业务对象
# ---------------------------------------------------------------

@dataclass
class AttendanceRecord:
    """从禅道抓到的一条打卡记录。"""
    date: date
    weekday: str            # '周一'..'周日'
    clock_in: str           # 'HH:MM'
    clock_out: str          # 'HH:MM'
    is_workday: bool        # 由 SHR 的"奋斗类型"字段决定，True=工作日

    @property
    def has_valid_punches(self) -> bool:
        return bool(self.clock_in and self.clock_out and ":" in self.clock_in and ":" in self.clock_out)


@dataclass
class OvertimeBill:
    """一张应提交的加班单。"""
    date: date
    weekday: str
    clock_in: str
    clock_out: str
    hours: float
    bill_type: str          # '工作日' | '非工作日'
    usage: str              # '奋斗积分' | '调休'
    content: str = ''       # 奋斗内容（用户填）
    submit_start: str = ''  # 可选：提交到 SHR 的奋斗开始时间 'HH:MM'
    submit_end: str = ''    # 可选：提交到 SHR 的加班结束时间 'HH:MM'
    rest_minutes: Optional[int] = None  # 可选：提交到 SHR 的休息时长（分钟）
    segment_index: int = 1
    segment_count: int = 1

    def to_line(self) -> str:
        """生成给用户看的一行摘要。"""
        segment = ""
        if self.segment_count > 1:
            segment = f"  分段={self.segment_index}/{self.segment_count}"
        submit_window = ""
        if self.submit_start and self.submit_end:
            submit_window = f"  提交时段={self.submit_start}-{self.submit_end}"
        return (
            f"{self.date} {self.weekday}  "
            f"{self.clock_in}-{self.clock_out}  "
            f"报 {self.hours:.1f}h  "
            f"[{self.bill_type}]  "
            f"使用方式={self.usage}"
            f"{segment}"
            f"{submit_window}"
            + (f"  | {self.content}" if self.content else "  | (待填奋斗内容)")
        )


def compute_bill(record: AttendanceRecord, prefer_compensation: bool = True) -> Optional[OvertimeBill]:
    """根据一条打卡记录生成加班单（不需提交则返回 None）。

    Args:
        record: 打卡记录
        prefer_compensation: 非工作日是否默认调休（True）。工作日不受此参数影响。
    """
    if not record.has_valid_punches:
        return None

    if record.is_workday:
        hours = calc_workday(record.clock_out)
        if hours is None:
            return None
        return OvertimeBill(
            date=record.date, weekday=record.weekday,
            clock_in=record.clock_in, clock_out=record.clock_out,
            hours=hours,
            bill_type='工作日',
            usage='奋斗积分',  # 工作日强制
        )
    else:
        hours = calc_holiday(record.clock_in, record.clock_out)
        if hours is None:
            return None
        return OvertimeBill(
            date=record.date, weekday=record.weekday,
            clock_in=record.clock_in, clock_out=record.clock_out,
            hours=hours,
            bill_type='非工作日',
            usage='调休' if prefer_compensation else '奋斗积分',
        )


MAX_SINGLE_SHR_HOURS = 8.0
SEGMENT_GAP_MINUTES = 1


def _non_workday_rest_minutes(start: time, end: time) -> int:
    """计算某个非工作日提交分段里的休息分钟数。"""
    rest = 0
    if start < LUNCH_START:
        rest += 60
    if start < DINNER_START and end >= DINNER_END:
        rest += 60
    return rest


def _segment_end_for_net_hours(start: time, hours: float, bill_type: str) -> tuple[time, int]:
    """根据净申报时长反推出 SHR 分段结束时间和休息分钟数。"""
    if bill_type == '非工作日':
        # 先估一次是否跨餐，再用扣餐后的 gross 时长算最终结束。
        probe_end = _add_hours(start, hours)
        rest = _non_workday_rest_minutes(start, probe_end)
        end = _add_hours(start, hours + rest / 60)
        rest = _non_workday_rest_minutes(start, end)
        return end, rest

    end = _add_hours(start, hours)
    return end, 0


def split_overtime_bill(bill: OvertimeBill,
                        max_hours: float = MAX_SINGLE_SHR_HOURS) -> list[OvertimeBill]:
    """把单日超过 SHR 单条上限的加班单拆成多个提交分段。

    SHR 对同一天单条奋斗时间有 8h 校验。超过 8h 时，必须拆成多条，
    且后续分段的奋斗开始时间要与上一段错开。

    >>> from datetime import date
    >>> b = OvertimeBill(date(2026,5,10), '周日', '09:44', '22:58', 11.0, '非工作日', '奋斗积分')
    >>> parts = split_overtime_bill(b)
    >>> [(p.hours, p.submit_start, p.submit_end, p.rest_minutes) for p in parts]
    [(8.0, '09:44', '18:44', 60), (3.0, '18:45', '21:45', 0)]
    >>> w = OvertimeBill(date(2026,5,9), '周六', '09:01', '22:06', 3.0, '工作日', '奋斗积分')
    >>> split_overtime_bill(w)[0] is w
    True
    """
    if bill.hours <= max_hours:
        return [bill]

    parts: list[OvertimeBill] = []
    remaining = bill.hours
    start = _parse_hhmm(bill.clock_in if bill.bill_type == '非工作日' else '19:00')
    idx = 1

    while remaining > 0:
        hours = min(max_hours, remaining)
        end, rest_minutes = _segment_end_for_net_hours(start, hours, bill.bill_type)
        parts.append(OvertimeBill(
            date=bill.date,
            weekday=bill.weekday,
            clock_in=bill.clock_in,
            clock_out=bill.clock_out,
            hours=hours,
            bill_type=bill.bill_type,
            usage=bill.usage,
            content=bill.content,
            submit_start=_format_hhmm(start),
            submit_end=_format_hhmm(end),
            rest_minutes=rest_minutes,
            segment_index=idx,
            segment_count=0,  # 回填
        ))
        remaining = round(remaining - hours, 2)
        idx += 1
        if remaining > 0:
            start = _add_hours(end, 0, SEGMENT_GAP_MINUTES)

    for p in parts:
        p.segment_count = len(parts)
    return parts


def split_long_overtime_bills(bills: list[OvertimeBill]) -> list[OvertimeBill]:
    """批量拆分超过 8h 的单日加班单。"""
    result: list[OvertimeBill] = []
    for bill in bills:
        result.extend(split_overtime_bill(bill))
    return result


def diff_against_submitted(bills: list[OvertimeBill],
                           submitted_dates: set[date]) -> list[OvertimeBill]:
    """从应提交清单里减去已提交日期，得到待提交清单。

    去重键：日期。同一天**已提交**则跳过（即使时长不一致），
    因为 SHR 不允许同日多单。

    >>> from datetime import date
    >>> b1 = OvertimeBill(date(2026,4,20), '周一', '08:46', '21:33', 2.5, '工作日', '奋斗积分')
    >>> b2 = OvertimeBill(date(2026,4,22), '周三', '08:49', '21:10', 2.0, '工作日', '奋斗积分')
    >>> remaining = diff_against_submitted([b1, b2], {date(2026,4,20)})
    >>> len(remaining)
    1
    >>> remaining[0].date
    datetime.date(2026, 4, 22)
    """
    return [b for b in bills if b.date not in submitted_dates]


# ---------------------------------------------------------------
# 命令行入口（用于本地测试）
# ---------------------------------------------------------------

if __name__ == "__main__":
    import doctest
    failures, tests = doctest.testmod(verbose=False)
    if failures:
        print(f"❌ doctest 失败 {failures}/{tests}")
        raise SystemExit(1)
    print(f"✅ 全部 {tests} 个 doctest 通过")
