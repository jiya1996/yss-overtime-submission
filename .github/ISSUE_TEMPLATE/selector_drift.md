---
name: 🔀 Selector 漂移（SHR / 禅道 UI 改版）
about: 因为系统升级导致脚本找不到元素、抓不到数据、点不到按钮
title: "[Selector] "
labels: selector-drift
---

## 哪一步开始失效

- [ ] 抓禅道打卡（`extract_attendance.py`）
- [ ] 抓 SHR 已提交（`extract_submitted.py`）
- [ ] 抓禅道工时（`extract_effort.py`）
- [ ] 提交加班单填表（`submit_overtime.py`）
  - [ ] 点不开「创建 ▾」下拉
  - [ ] 找不到「多条创建」选项
  - [ ] 网格「新增」按钮失效
  - [ ] 单元格 `td[aria-describedby=...]` 找不到
  - [ ] 奋斗积分下拉抓不到
  - [ ] 顶部「提交」按钮失效
  - [ ] messenger 弹窗确认按钮抓不到
- [ ] 其他：（描述）

## 系统版本

- SHR / 金蝶 s-HR：（管理员 → 关于 里能看到版本号；或贴 URL footer 的版本字符串）
- 禅道：（首页底部「powered by ZenTao …」字串）

## 出错时的具体输出

```
（粘贴报错堆栈或脚本控制台输出。注意脱敏：去除工号、单据号等）
```

## 你跑了哪个 dump 脚本？发现什么？

`scripts/debug/` 下的 dump 脚本是用来定位 selector 漂移的。请尝试跑对应那个：

```bash
cd scripts/debug
PYTHONIOENCODING=utf-8 PYTHONPATH=.. python debug_<name>.py
```

把 dump 输出贴出来（或者把变化的部分对比 `selectors.py` 里的常量贴出来）：

```
（粘贴 dump 结果。截图请上传到 issue 而不是贴本地路径）
```

## 你已经修好的 selector（如果有）

如果你已经定位到正确的新 selector，欢迎直接贴出来或提 PR：

```python
# 旧（在 scripts/selectors.py）
SHR_FILTER_QUERY_BTN_SEL = "#filter-search"

# 新
SHR_FILTER_QUERY_BTN_SEL = "..."
```

## 已脱敏

- [ ] 已确认贴出来的 dump / 截图不含工号、姓名、内部 URL、真实单据号
