---
name: yss-overtime-submission
description: 自动计算和提交赢时胜（YSS）公司的加班单（奋斗单）。当用户提到"提加班单"、"提奋斗单"、"算加班时长"、"SHR 加班"、"我要奋斗"、"禅道考勤"、"补提加班"、"这周加班还没提"等场景时，必须使用本 skill。会从禅道 OA 考勤数据自动抓取打卡记录，结合中国大陆法定节假日和调休补班（chinese_calendar 库）正确判断工作日类型，按公司规则（工作日 19 点后 / 节假日打卡到打卡 + 午晚餐扣除）计算应报时长，与 SHR 已提交奋斗单做差集，从禅道工时确认拉取奋斗内容候选，生成待提交清单后通过 Playwright 半自动提交到金蝶 s-HR Cloud。
author: jiya1996
version: 2.1
last_verified: 2026-05-12
---

# 赢时胜加班单提交助手

> **创建人**：jiya1996
> **最后实测验证**：2026-05-12
> **版本**：2.1（补充单日超过 8h 的按开始时间拆分 + 分批提交）
>
> **分发给同事使用**：见 [`references/installation_for_colleagues.md`](references/installation_for_colleagues.md)
> 本 skill 遵循 [agentskills.io](https://agentskills.io) 开放标准，可装在 Claude Code / OpenClaw / Cursor / Goose 等 30+ 兼容客户端里。

## 这个 skill 解决什么问题

赢时胜员工每周需要把加班时长提交到 SHR 系统（金蝶 s-HR Cloud）的「我要奋斗」模块。整个流程涉及：

1. 从**禅道**（pm.example.com:8071）拉打卡数据
2. 按**公司规则**算出每天该报多少加班时长
3. 从 **SHR**（oa.example.com:5887）查已提交的奋斗单做差集
4. 从禅道**工时确认**页拉当天做的事（用作奋斗内容）
5. 在 SHR「多条创建」里逐条填表 + 提交

整个流程做成「**人在环（HITL）的半自动化**」：计算和填表自动化，提交前用户人工 review。

## 何时使用本 skill

触发条件（任一即可）：
- 用户提到"提加班单"、"提奋斗单"、"算加班"、"我要奋斗"
- 用户问"这周加班几小时"、"还有哪几天没提加班"
- 用户提到 SHR / 金蝶 / <your-company> 加班相关
- 用户说"帮我把上周加班补一下"

## ⚠️ 必读前置警告

### 1. 节假日库每年要更新一次
本 skill 用 [`chinese-calendar`](https://pypi.org/project/chinese-calendar/) 库识别中国大陆**法定节假日 + 调休补班**。该库每年初待国务院公布次年放假安排后由维护者更新。

**每年元旦后第一次跑 skill 前，运行**：
```bash
python -m pip install -U chinese-calendar
```
否则跨年的日期判断会回落到「周一~周五 = 工作日」简单逻辑，**调休补班和法定假日全算错**。`scripts/holidays.py` 里已经做了 NotImplementedError 兜底 + warning，但你不会想要那个。

### 2. 公司可能禁用 RPA
金蝶 s-HR 可能埋点检测自动化操作。本次（2026-05-08）实测可用，不代表长期安全。**用前最好和 IT/HR 确认一句**——哪怕用自己账号操作。

### 3. Windows 控制台编码
Windows cmd / git-bash 默认 cp936，撞中文 + emoji 必崩。所有 Python 脚本必须加：
```bash
PYTHONIOENCODING=utf-8 python ...
```

### 4. 永远不要全自动提交
`submit_overtime.py` 必须传 `--confirm` 才会真正点提交按钮。`orchestrator.py` 走完所有阶段会暂停问 `yes` 才提交。

## 整体架构

```
┌────────────────────────────────────────────────────┐
│ 用户保持登录的 Chrome（手动过验证码 + 记密码）        │
│   (启动方式见 references/chrome_setup.md)          │
│   ├─ 禅道 tab    https://pm.example.com:8071       │
│   └─ SHR  tab    https://oa.example.com:5887       │
└─────────────────────┬──────────────────────────────┘
                      │ Chrome DevTools Protocol (CDP, port 9222)
                      ▼
┌────────────────────────────────────────────────────┐
│ Playwright（connect_over_cdp，复用登录态）          │
│   ├─ 抓禅道考勤打卡 (extract_attendance.py)         │
│   ├─ 抓 SHR 已提交奋斗单 (extract_submitted.py)     │
│   ├─ 抓禅道工时确认（奋斗内容）(extract_effort.py)   │
│   └─ 多条创建网格填表 + 提交 (submit_overtime.py)    │
└─────────────────────┬──────────────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────────────┐
│ 计算 + 节假日识别                                    │
│   ├─ calculator.py：工作日/非工作日规则、向下取整    │
│   └─ holidays.py：chinese_calendar 调休补班识别     │
└────────────────────────────────────────────────────┘
```

**SHR 的三个关键 URL**（金蝶 s-HR 是 SPA，每个页面 uipk 不一样）：
- 默认入口：`uipk=...AtsOverTimeBillForm` ← **空白单条新建表单（干扰页）**
- 列表页：`uipk=...AtsOverTimeBillList` ← **抓已提交清单 + 入口枢纽**
- 多条创建：`uipk=...AtsOverTimeBillForm.PersonnalBatch&method=addNew` ← **真正提交的网格**

## 标准使用流程

### 阶段 0：一次性环境准备

1. 按 [`references/chrome_setup.md`](references/chrome_setup.md) 启动带 `--remote-debugging-port=9222` 的 Chrome
2. 安装依赖：
   ```bash
   python -m pip install -r requirements.txt
   python -m playwright install chromium
   ```
3. 在 Chrome 里手动登录禅道 + SHR（过验证码、勾「记住密码」）
4. 自检：日常浏览器访问 `http://localhost:9222`，能看到禅道和 SHR 两个 tab

### 阶段 1：算时长 + 查差集（dry-run）

```bash
PYTHONIOENCODING=utf-8 python scripts/orchestrator.py \
    --start 2026-05-04 --end 2026-05-10 \
    --content "<你这周加班期间做的事>" \
    --dry-run-only
```

orchestrator 会：
1. 抓禅道考勤打卡
2. 抓 SHR 已提交奋斗单
3. 计算应提交差集；单日超过 8h 时自动按开始时间拆分多条（如 09:44-18:44 8h + 18:45-21:45 3h）
4. 填奋斗内容（**优先级**：`--content` 命令行 > 用户终端输入 > 禅道工时确认页拉建议）
5. 把待提交清单存到 `plan.json`，dry-run 输出后退出

**奋斗内容来源策略**（无默认占位，必须三选一拿到，否则报错退出）：
- 跑命令时加 `--content "..."` 一次性给所有单子填同样内容
- 不加 `--content` 时，会对每条单子先尝试从禅道**工时确认**页拉当天的任务名作为建议
- 禅道工时为空 → 终端会要求你手输（必填）

输出格式（示例）：
```
=== DRY RUN：以下 N 条**不会**真实提交 ===
  • 2026-MM-DD 周X  HH:MM-HH:MM  报 X.Xh  [工作日/非工作日]  使用方式=...  分段=1/2  提交时段=HH:MM-HH:MM  | <奋斗内容>
```

### 阶段 2：确认无误后真正提交

```bash
PYTHONIOENCODING=utf-8 python scripts/submit_overtime.py \
    --plan plan.json --confirm
```

或一键：
```bash
PYTHONIOENCODING=utf-8 python scripts/orchestrator.py \
    --start 2026-05-04 --end 2026-05-10 \
    --content "<填你这周加班做的事>" --confirm
```

提交流程：
1. goto `SHR_BILL_MULTI_CREATE_URL` 直达多条创建网格
2. 对每条单子：点 `#addRow_entries` → 填日期 → 等金蝶自动带类型/开始时间/使用方式 → 选积分下拉 → 填备注
   - 若该日总时长超过 8h，脚本会把同一天拆成多条，并覆盖 SHR 自动带出的奋斗开始/结束时间、休息时长和隐藏申请时长缓存。
   - 后续分段的开始时间必须和前一段不同（小时、分钟都建议错开 1 分钟），否则 SHR 会报「奋斗时间不能超过8个小时」。
3. 点顶部 `#submit` 按钮 → 弹金蝶 messenger 确认 → 点「确认」 a 标签
4. URL 跳到 `AtsOverTimeBillList` = 提交成功

成功后到 SHR 列表页二次核对。

## 计算规则速查

详见 [`references/calculation_rules.md`](references/calculation_rules.md)。

**工作日（含调休补班）**：
- 仅可申请奋斗积分
- 加班 = 下班打卡 − 19:00
- 必须 ≥ 1h 才能提交（exact 1h 可以提）
- 向下取整到 0.5h

**非工作日（含法定假日）**：
- 默认调休（可改奋斗积分）
- 加班 = 下班打卡 − 上班打卡 − 午晚餐扣除
- 午餐扣除：上班打卡 < 12:00 时扣 1h
- 晚餐扣除：下班打卡 ≥ 19:00 时扣 1h
- 单日净时长 > 8h：自动拆分多条，默认第一条最多 8h，第二条从上一条结束后 1 分钟开始

## 文件结构

```
yss-overtime-submission/
├── SKILL.md                           # 本文件
├── requirements.txt                   # playwright + chinese-calendar
├── references/
│   ├── calculation_rules.md           # 计算规则全集
│   ├── chrome_setup.md                # 启动 Chrome debug 模式
│   └── system_navigation.md           # 禅道 / SHR 真实 URL + selector 对照表
└── scripts/
    ├── calculator.py                  # 纯计算逻辑（带 doctest）
    ├── holidays.py                    # chinese_calendar 包装 + 调休补班识别
    ├── selectors.py                   # 集中管理 CSS selectors（UI 改版改这里）
    ├── connect_chrome.py              # Playwright CDP 连接工具
    ├── extract_attendance.py          # 抓禅道打卡
    ├── extract_submitted.py           # 抓 SHR 已提交单
    ├── extract_effort.py              # 抓禅道工时确认（奋斗内容候选）
    ├── submit_overtime.py             # 提交加班单（dry-run / confirm）
    ├── orchestrator.py                # 总入口
    ├── simulate.py                    # 不连浏览器的逻辑模拟（mock 数据）
    └── debug/                         # selector 漂移时复用的 dump 脚本
        ├── debug_shr.py               # 列表页 dump
        ├── debug_shr_list.py          # 点奋斗列表按钮 + dump
        ├── debug_shr_filter.py        # 展开筛选 + dump 日期 input
        ├── debug_shr_query.py         # 查询 + dump 表格行
        ├── debug_shr_multi_create.py  # dump 多条创建网格
        ├── debug_zt_effort.py         # dump 禅道工时确认页
        └── debug_zt_effort_5_6.py     # 拉某天工时（输出 demo）
```

## Selector 失效时的修复流程

UI 改版让脚本失效是迟早的事。修复步骤：

1. 在 debug Chrome 里访问出问题的页面
2. 跑 `scripts/debug/` 里对应的 dump 脚本（5 个 dump 脚本对应 5 个关键页面）
3. 比对输出，定位错位的 selector
4. 改 `scripts/selectors.py` 里对应的常量
5. 跑 `python scripts/orchestrator.py --start ... --end ... --dry-run-only` 自测

**所有 selector 集中在 `scripts/selectors.py`**——一处出错只改一处。

## 已知坑（实跑踩过）

| 坑 | 解决 |
|---|---|
| `goto AtsOverTimeBillForm` 直接进了一个**空白表单干扰页**，不是奋斗列表 | 用 `AtsOverTimeBillList` 直达列表页 |
| 列表页默认收起筛选，要先点「展开筛选」按钮才有日期 input | 脚本里先 `get_by_text("展开筛选").click()` |
| 顶部「奋斗列表」按钮 `#returnToOverTimeBillList` 是 `not visible`（被父容器遮住），普通 click 失效 | 用 `page.evaluate("...click()")` JS 兜底 |
| 列表页的「查询」按钮用 `get_by_text("查询")` 会误匹配到「未查询到结果」div | 用 `#filter-search` |
| 多条创建网格的 cell selector 不是 `data-field`，是 jqGrid 的 `aria-describedby="entries_*"` | 用 `td[aria-describedby="entries_otDate"]` 等 |
| 提交后弹的不是 native dialog，是金蝶 messenger 容器（`page.on("dialog")` 抓不到） | 找 `[class*="messenger"]` 里的「确认」 a 标签 click |
| 禅道工时页的「名称」「描述」是 `<input value="...">` 不是 td 文本 | 用 `td.querySelector('input').value` |
| 禅道工时 URL 不是 `m=effort&f=mywork`，是 `m=todo&f=confirmuserconsumed` | 已修正 selectors.py |
| 单日加班超过 8h 时，同一张单里第二条如果沿用 SHR 自动带出的同一开始时间，会报「奋斗时间不能超过8个小时」 | 按起始时间拆分多条，第二段从上一段结束后 1 分钟开始，并同步更新 jqGrid data / row currentData / storeValue 三处缓存 |
