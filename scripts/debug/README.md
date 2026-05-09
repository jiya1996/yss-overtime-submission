# Debug 脚本目录

> 这些脚本是 2026-05-08 实跑时用来 dump 页面结构的工具。
> 平时不用跑；selector 漂移或 UI 改版时拿来定位。
>
> **运行方式**（关键：要把父目录 `scripts/` 加到 PYTHONPATH，因为依赖 `selectors`/`connect_chrome`）：
>
> ```bash
> cd scripts/debug
> PYTHONIOENCODING=utf-8 PYTHONPATH=.. python debug_<name>.py
> ```

## 脚本作用速查

| 脚本 | 用途 | 输出 |
|---|---|---|
| `debug_shr.py` | goto BillList URL，dump 主 frame body + iframe 列表 | 系统临时目录下 `shr_debug.png` + 控制台 |
| `debug_shr_list.py` | 模拟从空白表单页点「奋斗列表」按钮，dump 真列表页表头 + 按钮 | `shr_list.png` |
| `debug_shr_filter.py` | 列表页展开筛选，dump 日期 input + 查询按钮 selector | `shr_filter.png` |
| `debug_shr_query.py` | 列表页设日期 + 查询，dump 数据行（jqgrow）| `shr_query.png` |
| `debug_shr_multi_create.py` | 点「创建 ▾ → 多条创建」，dump 网格 cell 的 aria-describedby | `shr_multi_create.png` |
| `debug_zt_effort.py` | goto 禅道工时确认页，dump 表头 + 数据行 | `zt_effort_initial.png` + `zt_effort_after.png` |
| `debug_zt_effort_5_6.py` | 拉某天工时数据示例（5/6）| `zt_effort_5_6.png` + 控制台 |
| `fill_shr_5_6.py` | 多条创建网格里加一行 + 填日期（中间产物，仅历史保留）| `shr_filled.png` |
| `fill_shr_5_6_v2.py` | 完整填表：日期 + 积分下拉 + 备注 | `shr_filled_full.png` |
| `submit_5_6.py` | 点顶部「提交」 + dump messenger 弹窗 | `shr_pre_submit.png` + `shr_post_submit.png` |
| `submit_5_6_confirm.py` | 点 messenger 里的「确认」完成提交 | `shr_after_confirm.png` |

## 这些脚本的价值

它们记录了**真实页面 dump 后的关键 selector**，是 `selectors.py` 准确性的来源。

**当 SHR / 禅道改版导致脚本失效时**，跑对应的 dump 脚本，对照新的 DOM 输出找正确 selector，回填到 `scripts/selectors.py`。

## 已知约束

- 所有脚本依赖 Chrome 已用 `--remote-debugging-port=9222` 启动且登录禅道 / SHR
- 截图输出到**系统临时目录**下的 `yss_skill_debug/`（跨平台跨用户，由 `_debug_utils.py` 处理）
  - Windows：`C:\Users\<你>\AppData\Local\Temp\yss_skill_debug\`
  - Mac/Linux：`/tmp/yss_skill_debug/`
  - 跑 `python _debug_utils.py` 可以看到具体路径
- 脚本 import `selectors` 和 `connect_chrome`（在父目录 `scripts/`），所以 **`PYTHONPATH=..` 是必需的**
