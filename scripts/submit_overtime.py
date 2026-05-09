"""
提交加班单到 SHR
==================

⚠️ **这是整个 skill 唯一会修改公司系统数据的脚本**。
   默认 dry-run，必须显式传 --confirm 才会真正点提交按钮。

实测流程（2026-05-08 跑通）：
1. goto SHR_BILL_MULTI_CREATE_URL（直达多条创建页）
2. 对每条单子：
   a. 点 #addRow_entries 加一行
   b. 在 td[aria-describedby="entries_otDate"] 里填日期 → 自动带出类型/开始时间/使用方式
   c. 在 td[aria-describedby="entries_strugglePoints"] 里点开下拉 → 选 1.5/2/...
   d. 在 td[aria-describedby="entries_description"] 里填备注（奋斗内容）
3. 点顶部 #submit
4. 在 messenger 弹窗里点「确认」 a 标签
5. URL 跳到 BillList = 提交成功

设计原则：
- 必须 dry-run 优先：先打印将要做的所有操作，等用户 OK 才执行
- 单条失败不影响其他：每条单独 try/except，记录哪些成功哪些失败
- 提交后跳转列表页 = 成功信号
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date as Date
from typing import List, Dict, Any

from calculator import OvertimeBill
from connect_chrome import find_or_open_tab, get_browser_context
from selectors import (
    SHR_BILL_MULTI_CREATE_URL,
    SHR_URL_PREFIX,
    SHR_GRID_BTN_ADD_ID,
    SHR_CELL_DATE_ARIA,
    SHR_CELL_POINTS_ARIA,
    SHR_CELL_DESC_ARIA,
    SHR_CELL_USAGE_ARIA,
    SHR_BTN_SUBMIT_TOP_ID,
    SHR_CONFIRM_DIALOG_OK_TEXT,
    SHR_USAGE_OPTION_TIAOXIU,
)


def submit_bills(bills: List[OvertimeBill],
                 confirm: bool = False,
                 verbose: bool = True) -> Dict[str, Any]:
    """通过 SHR 多条创建提交一批加班单。

    Args:
        bills: 待提交的加班单列表
        confirm: True 才真正点提交；False 仅 dry-run（打印不做）
        verbose: 打印详细操作

    Returns:
        {"submitted": [date, ...], "failed": [...], "dry_run": bool}
    """
    result: Dict[str, Any] = {"submitted": [], "failed": [], "dry_run": not confirm}

    if not bills:
        print("📭 没有待提交的单据，跳过")
        return result

    # === Dry-run 输出 ===
    print()
    print("=" * 70)
    if confirm:
        print(f"⚠️  即将真实提交 {len(bills)} 条加班单到 SHR：")
    else:
        print(f"🧪 DRY RUN：以下 {len(bills)} 条**不会**真实提交")
    print("=" * 70)
    for b in bills:
        print(f"  • {b.to_line()}")
        if not (b.content or "").strip():
            print(f"    ⚠️  这条没填奋斗内容（备注），提交会失败！")
    print("=" * 70)

    if not confirm:
        print("\n如需真正提交，加 --confirm 参数重跑。")
        return result

    # === 真实提交 ===
    with get_browser_context() as ctx:
        page = find_or_open_tab(ctx, SHR_URL_PREFIX,
                                SHR_BILL_MULTI_CREATE_URL)
        page.goto(SHR_BILL_MULTI_CREATE_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        try:
            page.wait_for_load_state("networkidle", timeout=12000)
        except Exception:
            pass
        page.wait_for_timeout(1500)

        # 逐条填表（每条点一次新增加一行，再填新行）
        for idx, bill in enumerate(bills):
            try:
                _add_and_fill_row(page, bill, row_idx=idx, verbose=verbose)
            except Exception as e:
                print(f"  ❌ 第 {idx + 1} 条 {bill.date} 填表失败：{e}")
                result["failed"].append({"date": str(bill.date), "error": str(e)})
                # 不要继续，整批要么全填要么停下让用户处理
                return result

        # 点顶部提交
        if verbose:
            print("\n🚀 点顶部「提交」按钮...")
        try:
            page.evaluate(f"document.getElementById('{SHR_BTN_SUBMIT_TOP_ID}').click()")
            page.wait_for_timeout(1500)
        except Exception as e:
            print(f"  ❌ 提交按钮点击失败：{e}")
            result["failed"].append({"step": "click_submit", "error": str(e)})
            return result

        # 等 messenger 弹窗 → 点「确认」
        if verbose:
            print("等 messenger 弹窗...")
        try:
            page.wait_for_timeout(1500)
            clicked = page.evaluate(f"""
                (function(){{
                   var btns = document.querySelectorAll('button, a');
                   for (var i = 0; i < btns.length; i++) {{
                      var b = btns[i];
                      if (!b.innerText) continue;
                      var t = b.innerText.trim();
                      if (t !== '{SHR_CONFIRM_DIALOG_OK_TEXT}' && t !== '确定') continue;
                      if (b.offsetParent === null) continue;
                      if (b.closest('td')) continue;
                      if (b.closest('.messenger, [class*="messenger"], [class*="modal"], [class*="dialog"]')) {{
                         b.click();
                         return 'ok';
                      }}
                   }}
                   return null;
                }})()
            """)
            if not clicked:
                print("  ⚠️  没找到 messenger 确认按钮，可能弹窗没出现或已关闭")
        except Exception as e:
            print(f"  ⚠️  确认弹窗处理失败：{e}")

        # 等跳转
        page.wait_for_timeout(3000)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(2000)

        # 验证：URL 跳到 BillList = 提交成功
        if "AtsOverTimeBillList" in page.url:
            print(f"✅ 已提交，URL 跳转到列表页。请到 SHR 二次核对。")
            result["submitted"] = [str(b.date) for b in bills]
        else:
            print(f"⚠️  提交后 URL 未跳转：{page.url}")
            print(f"   可能提交失败，请人工检查 SHR。")
            result["failed"].append({
                "step": "verify",
                "error": f"URL did not redirect to BillList: {page.url}"
            })

    return result


def _add_and_fill_row(page, bill: OvertimeBill, row_idx: int,
                     verbose: bool = True) -> None:
    """点新增加一行，然后在新行里填日期/积分/使用方式/备注。

    注意：每点一次「新增」会在网格末尾加一行，所以新行就是当前最后一行。
    """
    if verbose:
        print(f"\n  [行 {row_idx + 1}] 填 {bill.date} {bill.weekday} "
              f"{bill.hours}h {bill.usage}")

    # 1. 点新增
    page.evaluate(f"document.getElementById('{SHR_GRID_BTN_ADD_ID}').click()")
    page.wait_for_timeout(1200)

    # 2. 找到新加的那一行（最后一个 jqgrow，且不是 firstrow 占位行）
    # 用 :last-of-type 不够稳，用 nth-last
    target_row_sel = f"tr.jqgrow:not(.jqgfirstrow):nth-last-child(1)"

    # 3. 填奋斗日期 → 触发 autofill
    if verbose:
        print(f"     · 填奋斗日期 {bill.date}")
    cell_date = f'{target_row_sel} td[aria-describedby="{SHR_CELL_DATE_ARIA}"]'
    page.locator(cell_date).first.click(timeout=3000)
    page.wait_for_timeout(400)
    page.locator(f'{cell_date} input').first.fill(bill.date.isoformat())
    page.locator(f'{cell_date} input').first.press("Tab")
    page.wait_for_timeout(1500)  # 等 autofill 完成

    # 4. 选奋斗积分（下拉）
    if verbose:
        print(f"     · 选奋斗积分 {bill.hours}")
    cell_points = f'{target_row_sel} td[aria-describedby="{SHR_CELL_POINTS_ARIA}"]'
    page.locator(cell_points).first.click(timeout=3000)
    page.wait_for_timeout(700)
    points_text = f"{bill.hours:g}"  # 1.5 → "1.5"，2.0 → "2"
    clicked_points = page.evaluate(f"""
        (function(){{
           var lists = document.querySelectorAll('ul.dropdown-menu, ul[role="listbox"]');
           for (var i = 0; i < lists.length; i++) {{
              if (lists[i].offsetParent === null) continue;
              var items = lists[i].querySelectorAll('li, a');
              for (var j = 0; j < items.length; j++) {{
                 var t = items[j].innerText.trim();
                 if (t === '{points_text}') {{
                    items[j].click();
                    return true;
                 }}
              }}
           }}
           return false;
        }})()
    """)
    if not clicked_points:
        raise RuntimeError(f"奋斗积分下拉里没找到选项 {points_text}")
    page.wait_for_timeout(800)

    # 5. 使用方式（非工作日且选调休时才需要改；否则金蝶自动填了）
    if bill.usage == SHR_USAGE_OPTION_TIAOXIU:
        if verbose:
            print(f"     · 改使用方式为「调休」")
        cell_usage = f'{target_row_sel} td[aria-describedby="{SHR_CELL_USAGE_ARIA}"]'
        try:
            page.locator(cell_usage).first.click(timeout=3000)
            page.wait_for_timeout(700)
            # 在弹窗 / 下拉里点「调休」
            page.evaluate("""
                (function(){
                   var nodes = document.querySelectorAll('li, a, span, div');
                   for (var i = 0; i < nodes.length; i++) {
                      var n = nodes[i];
                      if (!n.innerText) continue;
                      if (n.innerText.trim() !== '调休') continue;
                      if (n.offsetParent === null) continue;
                      if (n.closest('table.ui-jqgrid-htable')) continue;  // 排除表头
                      n.click();
                      return true;
                   }
                   return false;
                })()
            """)
            page.wait_for_timeout(600)
        except Exception as e:
            if verbose:
                print(f"     ⚠️  改使用方式失败（继续，金蝶可能默认值已对）：{e}")

    # 6. 填备注（奋斗内容）
    content = (bill.content or "").strip()
    if not content:
        raise RuntimeError(
            f"{bill.date} 没有奋斗内容，金蝶要求必填。"
            "请在 orchestrator 阶段填好或用 --content 参数提供。"
        )
    if verbose:
        print(f"     · 填备注「{content}」")
    cell_desc = f'{target_row_sel} td[aria-describedby="{SHR_CELL_DESC_ARIA}"]'
    page.locator(cell_desc).first.click(timeout=3000)
    page.wait_for_timeout(400)
    desc_input = page.locator(f'{cell_desc} input, {cell_desc} textarea').first
    desc_input.fill(content)
    desc_input.press("Tab")
    page.wait_for_timeout(600)


def load_plan(path: str) -> List[OvertimeBill]:
    """从 JSON 加载待提交清单（orchestrator 生成的中间产物）。"""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    bills = []
    for d in data:
        bills.append(OvertimeBill(
            date=Date.fromisoformat(d["date"]),
            weekday=d["weekday"],
            clock_in=d["clock_in"],
            clock_out=d["clock_out"],
            hours=float(d["hours"]),
            bill_type=d["bill_type"],
            usage=d["usage"],
            content=d.get("content", ""),
        ))
    return bills


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, help="待提交清单 JSON 文件路径")
    parser.add_argument("--confirm", action="store_true",
                        help="加这个参数才会真正提交，否则只 dry-run")
    args = parser.parse_args()

    bills = load_plan(args.plan)
    submit_bills(bills, confirm=args.confirm)
