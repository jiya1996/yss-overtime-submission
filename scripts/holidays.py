"""
中国大陆节假日 + 调休补班检测
================================

核心需求：判断某一天对赢时胜员工是否是"工作日"（按公司 SHR 系统的定义）。
这不能用简单的"周一到周五"——中国节假日有调休补班机制：
  - 周六周日可能是工作日（春节/国庆调休补班）
  - 周一周二可能是节假日

依赖：chinese_calendar (https://pypi.org/project/chinese-calendar/)
   覆盖 2004 ~ 2026（库 1.11.0 版本）。每年初官方放假安排公布后，
   该库的维护者会发新版本——升级 pip 包即可。

降级策略：
  - 如果库覆盖该日期 → 用库的判断（最准）
  - 如果不覆盖（比如 2027+ 年还没更新）→ 回落到周一~周五简单判断 + WARN
"""

from __future__ import annotations

import warnings
from datetime import date as Date
from typing import Optional


def _fallback_is_workday(d: Date) -> bool:
    """周一~周五 = 工作日（不含节假日和调休判断）。"""
    return d.weekday() < 5  # Monday=0, Sunday=6


def is_workday(d: Date, *, warn_on_fallback: bool = True) -> bool:
    """判断指定日期是否为工作日（考虑中国法定节假日和调休补班）。

    Returns:
        True = 工作日（包括周日补班的情况）
        False = 节假日或休息日（包括因调休而休的工作日）

    >>> from datetime import date
    >>> is_workday(date(2025, 1, 1))  # 元旦
    False
    >>> is_workday(date(2025, 1, 26))  # 春节调休补班（周日上班）
    True
    >>> is_workday(date(2025, 5, 1))  # 劳动节
    False
    >>> is_workday(date(2025, 4, 7))  # 普通周一
    True
    >>> is_workday(date(2025, 4, 5))  # 普通周六
    False
    """
    try:
        import chinese_calendar
        return chinese_calendar.is_workday(d)
    except ImportError:
        if warn_on_fallback:
            warnings.warn(
                "chinese_calendar 库未安装，回落到简单的周一~周五判断。"
                "调休补班和法定假日会算错。请运行 `pip install chinese-calendar`。",
                stacklevel=2,
            )
        return _fallback_is_workday(d)
    except NotImplementedError:
        if warn_on_fallback:
            warnings.warn(
                f"chinese_calendar 库尚未覆盖 {d.year} 年的放假安排，"
                "回落到周一~周五判断。请运行 `pip install -U chinese-calendar` 升级。",
                stacklevel=2,
            )
        return _fallback_is_workday(d)


def get_day_label(d: Date) -> str:
    """返回人类可读的"工作日 / 非工作日 + 原因"标注（用于打印）。

    >>> from datetime import date
    >>> get_day_label(date(2025, 1, 1))
    '非工作日（元旦）'
    >>> get_day_label(date(2025, 4, 5))
    '非工作日（清明节）'
    >>> get_day_label(date(2025, 4, 12))  # 真·普通周六
    '非工作日（周六）'
    >>> get_day_label(date(2025, 1, 26))
    '工作日（春节调休补班）'
    """
    try:
        import chinese_calendar
        from chinese_calendar import is_holiday, get_holiday_detail

        weekday_name = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][d.weekday()]

        if is_workday(d, warn_on_fallback=False):
            # 工作日 → 看是不是周末补班
            if d.weekday() >= 5:  # 周六或周日
                # 是周末但被识别为工作日 → 必然是调休补班
                # 反查最近的假日来标注是哪个假期的补班
                nearby_holiday = _find_nearby_holiday_name(d)
                if nearby_holiday:
                    return f"工作日（{nearby_holiday}调休补班）"
                return "工作日（调休补班）"
            return f"工作日（{weekday_name}）"
        else:
            # 非工作日 → 看是节假日还是普通周末
            on_holiday, holiday_name = get_holiday_detail(d)
            if on_holiday and holiday_name:
                return f"非工作日（{_translate_holiday_name(holiday_name)}）"
            return f"非工作日（{weekday_name}）"
    except (ImportError, NotImplementedError):
        weekday_name = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][d.weekday()]
        if _fallback_is_workday(d):
            return f"工作日（{weekday_name}，⚠️ 未识别节假日）"
        return f"非工作日（{weekday_name}）"


_HOLIDAY_NAME_CN = {
    'New Years Day': '元旦',
    "New Year's Day": '元旦',
    'Spring Festival': '春节',
    'Tomb-sweeping Day': '清明节',
    'Labour Day': '劳动节',
    'Dragon Boat Festival': '端午节',
    'Mid-autumn Festival': '中秋节',
    'National Day': '国庆节',
}


def _translate_holiday_name(en: str) -> str:
    return _HOLIDAY_NAME_CN.get(en, en)


def _find_nearby_holiday_name(d: Date) -> Optional[str]:
    """找日期 d 附近 7 天内的节假日名（用于标注'XX调休补班'）。"""
    try:
        from chinese_calendar import is_holiday, get_holiday_detail
        from datetime import timedelta
        for offset in range(-7, 8):
            candidate = d + timedelta(days=offset)
            if candidate == d:
                continue
            on_holiday, name = get_holiday_detail(candidate)
            if on_holiday and name:
                return _translate_holiday_name(name)
    except Exception:
        pass
    return None


if __name__ == "__main__":
    import doctest
    failures, tests = doctest.testmod(verbose=False)
    if failures:
        raise SystemExit(f"❌ {failures}/{tests} 个 doctest 失败")
    print(f"✅ 全部 {tests} 个 doctest 通过")
