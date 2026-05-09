"""
所有页面的 selector 集中在这里。
==================================

UI 改版后只需要改这个文件。

⚠️ 部署到自己公司前，**必须**改下面 ZENTAO_HOST / SHR_HOST 两个常量，
   或者通过环境变量覆盖：
       export YSS_ZENTAO_HOST=pm.yourcompany.com:8071
       export YSS_SHR_HOST=oa.yourcompany.com:5887

⚠️ 本文件的 selector 是基于金蝶 s-HR Cloud + 禅道 OA 标准版实测验证。
   UI 改版导致 selector 失效时，参考 references/system_navigation.md
   末尾的「Selector 失效流程」+ 跑 scripts/debug/ 里对应 dump 脚本。
"""

import os

# ===========================================================
# 公司域名配置（部署前必改）
# ===========================================================
# 默认值是占位 example.com，clone 仓库后必须改成你公司的实际地址
ZENTAO_HOST = os.environ.get("YSS_ZENTAO_HOST", "pm.example.com:8071")
SHR_HOST = os.environ.get("YSS_SHR_HOST", "oa.example.com:5887")

# 用于 connect_chrome.find_or_open_tab() 的 url_prefix 参数（去掉端口号）
ZENTAO_URL_PREFIX = f"https://{ZENTAO_HOST.split(':')[0]}"
SHR_URL_PREFIX = f"https://{SHR_HOST.split(':')[0]}"


# ===========================================================
# 禅道 ZENTAO
# ===========================================================

# --- 考勤数据页（直接 URL 带日期参数，最稳）---
# 注意：第一行是 f-string（host 立即展开），后面是普通字符串
# {start} / {end} 留作 .format() 占位
ZT_ATTENDANCE_URL = (
    f"https://{ZENTAO_HOST}/index.php?m=kingdee&f=myclock"
    "&t=html&start={start}&end={end}"
)
ZT_ATTENDANCE_ROW_SEL = "table tbody tr"
ZT_COL_DATE_IDX = 0       # 日期列
ZT_COL_WEEKDAY_IDX = 1    # 星期列
ZT_COL_PUNCH_IDX = 2      # 打卡时间列（"08:46,21:33"）

# --- 工时确认页（用于拉奋斗内容）---
# 真实 URL 不是 m=effort&f=mywork，是这个：
ZT_EFFORT_URL = (
    f"https://{ZENTAO_HOST}/index.php?m=todo&f=confirmuserconsumed"
    "&day={date}"
)
ZT_EFFORT_DATE_INPUT_SEL = "#day"  # class Wdate，带日期切换
# 工时表格行（带 input 的数据行；表头在 thead）
ZT_EFFORT_ROW_SEL = "table.table-1 tbody tr, table.colored tbody tr"
# 列顺序：
#   0=ID 1=类型 2=编号 3=名称 4=状态 5=起止时间 6=时间暂定
#   7=工时 8=项目(维护说明) 9=客户 10=对应系统 11=任务类型 12=描述
ZT_EFFORT_COL_ID_IDX = 0
ZT_EFFORT_COL_TYPE_IDX = 1
ZT_EFFORT_COL_CODE_IDX = 2
ZT_EFFORT_COL_NAME_IDX = 3        # 名称（input.value）⭐
ZT_EFFORT_COL_STATUS_IDX = 4
ZT_EFFORT_COL_HOURS_IDX = 7       # 工时（input.value）⭐
ZT_EFFORT_COL_PROJECT_IDX = 8     # 项目维护说明
ZT_EFFORT_COL_SYSTEM_IDX = 10
ZT_EFFORT_COL_TASK_TYPE_IDX = 11
ZT_EFFORT_COL_DESC_IDX = 12       # 描述（input.value）⭐


# ===========================================================
# SHR / 金蝶 s-HR Cloud
# ===========================================================

SHR_HOME_URL = (
    f"https://{SHR_HOST}/shr/dynamic.do"
    "?uipk=shr.perself.homepage&inFrame=true&blank=true"
)

# --- 我要奋斗：三个关键页面 URL ---
# 1) 列表页（查已提交 + 入口枢纽）⭐
SHR_BILL_LIST_URL = (
    f"https://{SHR_HOST}/shr/dynamic.do"
    "?uipk=com.kingdee.eas.hr.ats.app.AtsOverTimeBillList"
    "&inFrame=true&billId="
)

# 2) 单条新建表单页（默认进入「我要奋斗」时落到这里——空白干扰页）
SHR_BILL_FORM_URL = (
    f"https://{SHR_HOST}/shr/dynamic.do"
    "?uipk=com.kingdee.eas.hr.ats.app.AtsOverTimeBillForm"
    "&inFrame=true&fromHeader=true"
)

# 3) 多条创建直达 URL（脚本提交单子用这个）⭐
SHR_BILL_MULTI_CREATE_URL = (
    f"https://{SHR_HOST}/shr/dynamic.do"
    "?uipk=com.kingdee.eas.hr.ats.app.AtsOverTimeBillForm.PersonnalBatch"
    "&inFrame=true&billId=&method=addNew"
)

# 在表单页跳列表页的按钮 id（hidden，需要 JS click 兜底）
SHR_BTN_RETURN_TO_LIST_ID = "returnToOverTimeBillList"

# --- 列表页筛选区 ---
SHR_BTN_EXPAND_FILTER_TEXT = "展开筛选"
SHR_FILTER_DATE_FROM_SEL = "#entries--otDate-datestart"   # ⭐
SHR_FILTER_DATE_TO_SEL = "#entries--otDate-dateend"       # ⭐
SHR_FILTER_DATE_PRESET_SEL = "#entries--otDate-dateselect"  # 「本周/本月/自定义」下拉
SHR_FILTER_QUERY_BTN_SEL = "#filter-search"               # ⭐ 查询按钮（不是 get_by_text("查询")，会误匹配）

# --- 列表页表格（jqGrid）---
SHR_LIST_ROW_SEL = "tr.jqgrow"  # 数据行；jqgfirstrow 是空的占位行
SHR_LIST_FIRSTROW_CLS = "jqgfirstrow"  # 用来排除占位行
# 列顺序（从 dump th 验证）：
#   0=空 1=ID(隐藏) 2=单据编号 3=姓名 4=奋斗日期 5=奋斗开始时间
#   6=奋斗积分 7=奋斗积分(重复) 8=使用方式 9=加班结束时间
#   10=休息时长 11=奋斗原因 12=奋斗类型 13=单据状态
#   14=当前审批人 15=来源 16=单据提交类型 ...
SHR_LIST_COL_BILL_NO_IDX = 2
SHR_LIST_COL_NAME_IDX = 3
SHR_LIST_COL_DATE_IDX = 4         # 奋斗日期 ⭐
SHR_LIST_COL_START_TIME_IDX = 5
SHR_LIST_COL_HOURS_IDX = 6        # 奋斗积分（小时数）
SHR_LIST_COL_USAGE_IDX = 8
SHR_LIST_COL_END_TIME_IDX = 9
SHR_LIST_COL_OT_TYPE_IDX = 12     # 奋斗类型（工作日 / 非工作日）
SHR_LIST_COL_STATUS_IDX = 13      # 单据状态 ⭐
SHR_LIST_COL_AUDITOR_IDX = 14
SHR_LIST_COL_SOURCE_IDX = 15

# 已提交但被驳回 / 已撤回 的不算"已提交"
# 实测见到的状态值：审批中、审批通过、已撤回、驳回
SHR_STATUS_VALID = ["审批通过", "审批中", "待审批"]

# --- 列表页顶部按钮区（创建下拉）---
SHR_BTN_CREATE_SINGLE_ID = "addNew"        # 单条创建
SHR_BTN_CREATE_BATCH_ID = "addNewBatch"    # 多条创建
SHR_BTN_LIST_SUBMIT_TEXT = "提交"          # 列表里选中行批量提交（不是新建表单的提交）
SHR_BTN_LIST_DELETE_TEXT = "删除"
SHR_BTN_LIST_REVOKE_TEXT = "撤回"

# --- 多条创建网格（核心填表区）---
# 顶部按钮
SHR_GRID_BTN_ADD_ID = "addRow_entries"   # ⭐ 「新增」加一行
SHR_GRID_BTN_DEL_ID = "deleteRow_entries"

# 网格列用 aria-describedby 定位（jqGrid 标准）⭐
# 用法：page.locator(f'tr.jqgrow td[aria-describedby="{COL}"]')
SHR_CELL_PERSON_ARIA = "entries_person"
SHR_CELL_DATE_ARIA = "entries_otDate"            # 奋斗日期 ⭐ 填这个会自动带出类型/开始时间/使用方式
SHR_CELL_INTEGRAL_ARIA = "entries_integral"      # 积分（系统算）
SHR_CELL_POINTS_ARIA = "entries_strugglePoints"  # 奋斗积分 ⭐ 下拉选 1/1.5/2/...
SHR_CELL_OT_TYPE_ARIA = "entries_otType"         # 奋斗类型（自动）
SHR_CELL_START_ARIA = "entries_startTime"        # 奋斗开始时间（自动）
SHR_CELL_END_ARIA = "entries_endTime"            # 加班结束时间（积分填后自动）
SHR_CELL_REST_ARIA = "entries_restTime"          # 休息时长
SHR_CELL_APPLY_OT_ARIA = "entries_applyOTTime"
SHR_CELL_REASON_ARIA = "entries_otReason"        # 奋斗原因（默认"个人原因"）
SHR_CELL_USAGE_ARIA = "entries_otCompens"        # 使用方式（自动；非工作日可改）
SHR_CELL_DESC_ARIA = "entries_description"       # 备注（奋斗内容）⭐

# 奋斗积分下拉（点单元格后弹出）
SHR_POINTS_DROPDOWN_SEL = "ul.dropdown-menu.overflow-select"
# 下拉里的 li 文本就是 "1" / "1.5" / "2" / ... 用 page.locator(...).get_by_text(exact=True) 选

# 使用方式弹窗（非工作日时可选「调休」/「奋斗积分」）
SHR_USAGE_OPTION_TIAOXIU = "调休"
SHR_USAGE_OPTION_POINTS = "奋斗积分"

# --- 提交流程 ---
SHR_BTN_SUBMIT_TOP_ID = "submit"  # 顶部提交按钮（要排除 td 内的「提交」）
# 点提交后弹金蝶 messenger 确认对话框（不是 native dialog）
SHR_CONFIRM_DIALOG_CONTAINER_SEL = '.messenger-message, [class*="messenger"]'
SHR_CONFIRM_DIALOG_OK_TEXT = "确认"  # 在上面 container 里找「确认」 a 标签
