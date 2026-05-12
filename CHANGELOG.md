# Changelog

本仓库版本变更记录。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Planned
- Phase 2: 工作日志 → 自动填禅道工时 + 加班理由提取（用户已确认设计方向，待开发）

---

## [2.1.0] - 2026-05-12

### Added
- 单日加班净时长超过 8h 时自动拆分提交分段，并在 `plan.json` 中记录 `submit_start` / `submit_end` / `rest_minutes`。
- `submit_overtime.py` 支持把拆分分段的开始时间、结束时间、休息时长同步写入 SHR jqGrid 的真实缓存，避免只改 DOM 导致提交仍按旧时间校验。

### Changed
- 文档补充 SHR 超 8h 场景的实战规则：同一天多段必须按不同开始时间拆分，后续分段从上一段结束后 1 分钟开始。

---

## [2.0.0] - 2026-05-08

首次公开发布。基于内部实测结果重构后开源。

### Added
- 三个 SHR 关键 URL 区分（`AtsOverTimeBillForm` / `AtsOverTimeBillList` / `PersonnalBatch`）
- jqGrid `aria-describedby` cell selector 体系
- 金蝶 messenger 弹窗 confirm 处理（不是 native dialog）
- `orchestrator.py --content` 命令行参数（解决 bash 调用时 `input()` 拿不到 stdin）
- `chinese-calendar` 节假日识别（含调休补班）
- 11 个 debug 脚本归档到 `scripts/debug/`，用于 selector 漂移时复用
- `_debug_utils.py` 跨平台截图路径
- 完整文档：SKILL.md / chrome_setup.md / system_navigation.md / calculation_rules.md / installation_for_colleagues.md

### Changed
- **Breaking**: SHR 列表 URL 从 `AtsOverTimeBillForm`（空白表单干扰页）改为 `AtsOverTimeBillList`（真实列表页）
- **Breaking**: 列表筛选 selector 从 `input[placeholder*="开始"]` 等通用猜测改为精确 id（`#entries--otDate-datestart` 等）
- **Breaking**: 网格 cell 定位从 `data-field` 改为 `aria-describedby="entries_*"`（jqGrid 标准）
- 禅道工时确认 URL 从 `m=effort&f=mywork` 修正为 `m=todo&f=confirmuserconsumed`
- 列表查询按钮从 `get_by_text("查询")`（误匹配）改为 `#filter-search`
- 顶部「奋斗列表」按钮 `#returnToOverTimeBillList` 改用 JS click 兜底（普通 click "not visible" 失效）
- Host 配置抽离：`scripts/selectors.py` 顶部新增 `ZENTAO_HOST` / `SHR_HOST` 常量，支持 env var 覆盖
- Description 中性化：移除所有项目代号 / 工号 / 真实单据号 / 个人姓名

### Fixed
- `extract_effort.py` doctest 缺失 `description` 参数导致跑测 crash
- 禅道工时表「名称」「工时」「描述」三列必须取 `<input value>` 而非 `td.innerText`
- Windows 控制台 cp936 撞中文 emoji 必崩，所有脚本须 `PYTHONIOENCODING=utf-8`

### Removed
- `orchestrator.py` 中的硬编码奋斗内容默认占位（个人化数据）。改为强制三选一：`--content` / 终端输入 / 禅道工时建议；三者都拿不到 → 报错退出

### Verified
- 在金蝶 s-HR Cloud + 禅道 OA 标准版实测：单据通过审批
- 端到端测试：抓打卡 → 算时长 → 抓 SHR 已提交 → 差集 → 拉禅道工时建议 → 提交（含 messenger 弹窗确认）→ URL 跳列表页

---

## [1.0.0] - 2026-05-08 [Internal]

> 内部里程碑，未公开发布。

### Added
- 初版 skill 结构（SKILL.md + scripts/ + references/）
- Playwright + Chrome CDP 连接
- 工作日 / 非工作日加班时长规则
- SHR 多条创建网格填表（基于早期 selector 假设，多处不准）

### Issues
- selector 多处假设跟实际 UI 不符（v2.0 修正）
- 默认占位值含个人化内容（v2.0 移除）
