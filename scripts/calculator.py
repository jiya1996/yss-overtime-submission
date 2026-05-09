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
from dataclasses import dataclass, field
from datetime import date, datetime, time
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

    def to_line(self) -> str:
        """生成给用户看的一行摘要。"""
        return (
            f"{self.date} {self.weekday}  "
            f"{self.clock_in}-{self.clock_out}  "
            f"报 {self.hours:.1f}h  "
            f"[{self.bill_type}]  "
            f"使用方式={self.usage}"
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
