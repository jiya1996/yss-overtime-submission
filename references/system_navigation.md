# 禅道 + SHR 页面导航指南

> **最后实测验证**：2026-05-08
> **创建人**：jiya1996
>
> 本文档记录脚本要操作的每个页面的真实 URL、关键元素 selector、和数据格式。
> Selector 全部经过实跑验证，集中维护在 [`scripts/selectors.py`](../scripts/selectors.py)。

---

## 一、禅道（pm.example.com:8071）

### 1.1 OA 考勤数据页

**URL**（直达带日期参数，最稳）：
```
https://pm.example.com:8071/index.php?m=kingdee&f=myclock&t=html&start=YYYY-MM-DD&end=YYYY-MM-DD
```

**表格列**（`table tbody tr` 选择）：
| idx | 列 | 数据样例 |
|----|----|---------|
| 0 | 日期 | 2026-05-06 |
| 1 | 星期 | 周三 |
| 2 | 打卡时间 | 08:45,20:32（逗号分隔，单字符串）|

**坑**：
- 周末/节假日没打卡的行**打卡列为空**，需要判空跳过
- 只打了上班卡没打下班卡时，逗号分隔后只有 1 项

### 1.2 工时确认页（拉奋斗内容）

**真实 URL**（不是 `m=effort&f=mywork`）：
```
https://pm.example.com:8071/index.php?m=todo&f=confirmuserconsumed&day=YYYY-MM-DD
```
URL 直接带 `day=` 参数即可切换日期，不用模拟点日历。

**日期选择器**（如果想 UI 切日期）：`input#day.Wdate`

**表格列**（验证过的列序）：
| idx | 列 | 取值方式 |
|----|----|---------|
| 0 | ID | td.innerText |
| 1 | 类型 | td.innerText |
| 2 | 编号 | td.innerText |
| **3** | **名称** | **`td.querySelector('input').value`** ⭐ |
| 4 | 状态 | select.selectedOptions |
| 5 | 起止时间 | td.innerText（多个时间用 \n 分隔，取第一个）|
| 6 | 时间暂定 | checkbox |
| **7** | **工时** | **`td.querySelector('input').value`** ⭐ |
| 8 | 项目（维护说明）| td.innerText |
| 9 | 客户 | td.innerText |
| 10 | 对应系统 | td.innerText |
| 11 | 任务类型 | td.innerText |
| **12** | **描述** | **`td.querySelector('input').value`** ⭐ |

**关键坑**：「名称」「工时」「描述」是 `<input value="...">` 不是文本，必须取 input.value！

---

## 二、SHR / 金蝶 s-HR Cloud（oa.example.com:5887）

### 2.1 三个关键 URL（必须区分清楚）

金蝶 s-HR 是 SPA，每个页面 uipk 不一样：

| 用途 | URL uipk 部分 |
|---|---|
| 员工自助首页 | `shr.perself.homepage` |
| 单条新建表单（**默认入口**，干扰页）| `com.kingdee.eas.hr.ats.app.AtsOverTimeBillForm` |
| **奋斗单列表（抓已提交 + 入口枢纽）** ⭐ | `com.kingdee.eas.hr.ats.app.AtsOverTimeBillList` |
| **多条创建网格（提单专用）** ⭐ | `com.kingdee.eas.hr.ats.app.AtsOverTimeBillForm.PersonnalBatch` |

完整 URL 构造：
```
https://oa.example.com:5887/shr/dynamic.do?uipk={uipk}&inFrame=true&billId=&method=addNew
```

---

### 2.2 奋斗单列表页（查已提交）

**直达 URL**：
```
https://oa.example.com:5887/shr/dynamic.do?uipk=com.kingdee.eas.hr.ats.app.AtsOverTimeBillList&inFrame=true&billId=
```

**关键 selector**：

| 控件 | Selector |
|---|---|
| 「展开筛选」按钮 | `text="展开筛选"` |
| 起始日期 input | `#entries--otDate-datestart` |
| 结束日期 input | `#entries--otDate-dateend` |
| 日期 preset 下拉（本周/本月/自定义）| `#entries--otDate-dateselect` |
| 查询按钮 | `#filter-search` |
| 表格数据行 | `tr.jqgrow:not(.jqgfirstrow)` |
| 「创建」按钮（下拉容器）| `.btn-group:has-text("创建")` |
| 单条创建 li | `#addNew` |
| 多条创建 li | `#addNewBatch` |

**表格列序**（jqGrid，从表头 dump 验证）：
| idx | 列 |
|---|---|
| 0 | （checkbox）|
| 1 | ID（隐藏）|
| 2 | 单据编号 |
| 3 | 姓名 |
| **4** | **奋斗日期** ⭐ |
| 5 | 奋斗开始时间 |
| 6 | 奋斗积分（小时数）|
| 7 | 奋斗积分（重复列）|
| 8 | 使用方式 |
| 9 | 加班结束时间 |
| 10 | 休息时长(分钟) |
| 11 | 奋斗原因 |
| 12 | 奋斗类型 |
| **13** | **单据状态** ⭐ |
| 14 | 当前审批人 |
| 15 | 来源 |

**单据状态实测值**：审批中 / 审批通过 / 已撤回 / 驳回。

**有效已提交**（差集判重时算「已交」）：审批中 + 审批通过 + 待审批。
**无效**（视为未交，可重新提交）：已撤回 + 驳回。

**坑**：
- 默认筛选区是收起的，要先点「展开筛选」才有日期 input
- 默认日期范围是「本周」(`本周` 字样的下拉)；要查别的范围用 fill 起止 input
- 列表页**首屏数据可能是空的**（共0页），原因是默认 preset 没匹配到数据，**主动设日期+查询**才会出来

---

### 2.3 多条创建网格（提单专用）

**直达 URL** ⭐：
```
https://oa.example.com:5887/shr/dynamic.do?uipk=com.kingdee.eas.hr.ats.app.AtsOverTimeBillForm.PersonnalBatch&inFrame=true&billId=&method=addNew
```

**顶部按钮**：

| 按钮 | Selector |
|---|---|
| 提交（顶部）⭐ | `#submit`（要排除 `td` 内的）|
| 奋斗列表（返回列表页）| `#returnToOverTimeBillList`（hidden，需要 JS click）|

**网格按钮**：

| 按钮 | Selector |
|---|---|
| 新增（加一行）⭐ | `#addRow_entries` |
| 删除 | `#deleteRow_entries` |

**网格列**（jqGrid，关键：用 `aria-describedby` 定位单元格）⭐：

| 字段 | aria-describedby |
|---|---|
| 姓名（自动）| `entries_person` |
| **奋斗日期**（必填，触发 autofill）| `entries_otDate` |
| 积分（系统算）| `entries_integral` |
| **奋斗积分**（必填，下拉 1/1.5/2/...）| `entries_strugglePoints` |
| 奋斗类型（自动带出）| `entries_otType` |
| 奋斗开始时间（自动）| `entries_startTime` |
| 加班结束时间（自动）| `entries_endTime` |
| 休息时长 | `entries_restTime` |
| 申请加班时长 | `entries_applyOTTime` |
| 奋斗原因（默认"个人原因"）| `entries_otReason` |
| 使用方式（自动；非工作日可改）| `entries_otCompens` |
| **备注（奋斗内容）必录 ⭐** | `entries_description` |

**填表顺序很重要**（金蝶有 autofill 链）：
1. **先填奋斗日期** → 自动带出：奋斗类型 / 奋斗开始时间(19:00) / 使用方式(工作日=奋斗积分)
2. **填奋斗积分**（下拉点选 1.5/2/...）→ 自动带出：加班结束时间(19:00 + h)
3. **使用方式**：工作日不用动；非工作日想选「调休」要点单元格再选
4. **填备注**：奋斗内容，必填，金蝶不填会拒绝

**奋斗积分下拉**：
- 点 `td[aria-describedby="entries_strugglePoints"]` 弹下拉
- 下拉容器：`ul.dropdown-menu.overflow-select`
- 选项是 `<li>` 文本：`1`, `1.5`, `2`, ... 直到 `8`

**单元格内 input**（填值时用）：
```python
page.locator(f'td[aria-describedby="entries_otDate"] input').fill("2026-05-06")
```

---

### 2.4 提交流程

1. 点 `#submit`（顶部）
2. 金蝶弹 messenger 确认对话框：「您确认要提交吗？」+ 「确认」/「关闭」
   - 不是 native dialog，`page.on("dialog")` 抓不到
   - 容器：`.messenger-message` 或 `[class*="messenger"]`
   - 「确认」是 `<a>` 标签
3. 点「确认」 → 等 URL 跳到 `AtsOverTimeBillList` = 提交成功

**JS 找「确认」按钮**（避开 td 内的）：
```javascript
var btns = document.querySelectorAll('button, a');
for (var b of btns) {
   if (b.innerText.trim() !== '确认') continue;
   if (b.offsetParent === null) continue;
   if (b.closest('td')) continue;
   if (b.closest('[class*="messenger"]')) {
      b.click();
      break;
   }
}
```

---

## 三、登录态 / 验证码

| 系统 | 登录方式 | 验证码 |
|---|---|---|
| 禅道 | 工号/密码 + 验证码 | ✅ 有 |
| SHR | 工号/密码 + 验证码（首次）| ✅ 有，session 长 |

策略：用户每天**手动登录一次** debug Chrome，脚本通过 CDP（port 9222）复用。

---

## 四、Selector 失效后的快速修复流程

1. 在 debug Chrome 里访问出问题的页面
2. 跑对应的 dump 脚本（在 `scripts/debug/`）：
   - `debug_shr.py` → 列表页 DOM
   - `debug_shr_list.py` → 点奋斗列表按钮 + dump
   - `debug_shr_filter.py` → 展开筛选 + 日期 input
   - `debug_shr_query.py` → 查询 + 表格行
   - `debug_shr_multi_create.py` → 多条创建网格结构
   - `debug_zt_effort.py` → 禅道工时页结构
3. 对照 dump 输出找正确 selector
4. 改 `scripts/selectors.py`
5. 验证：
   ```bash
   PYTHONIOENCODING=utf-8 python scripts/orchestrator.py \
       --start YYYY-MM-DD --end YYYY-MM-DD --dry-run-only
   ```

**所有 selector 都集中在 `scripts/selectors.py`**——一处出错只改一处。

---

## 五、JS click 兜底模板

很多金蝶按钮 Playwright 判定 "not visible"（父容器有特殊 CSS）。强制点的兜底：

```python
# 三层兜底：normal click → force click → JS click
clicked = False
try:
    page.locator(selector).click(timeout=3000)
    clicked = True
except Exception:
    pass
if not clicked:
    try:
        page.locator(selector).click(force=True, timeout=3000)
        clicked = True
    except Exception:
        pass
if not clicked:
    page.evaluate(f"document.querySelector('{selector}').click()")
```

实测 `#returnToOverTimeBillList` 必须走 JS click。
