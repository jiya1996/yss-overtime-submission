<!-- 感谢提交 PR！请填写下面的清单。 -->

## 这个 PR 要解决什么问题

（一句话描述。如果对应一个 issue，写「Fixes #123」自动关联）

## 改动了什么

- [ ] 修 selector 漂移（`scripts/selectors.py`）
- [ ] 修计算逻辑（`scripts/calculator.py` / `holidays.py`）
- [ ] 改填表流程（`scripts/submit_overtime.py`）
- [ ] 改抓数据流程（`extract_*.py`）
- [ ] 文档（`SKILL.md` / `references/`）
- [ ] CI / 工具链 / 元信息（`.github/` / `requirements.txt` / `LICENSE`）
- [ ] 其他：

## 测试

如何验证这个改动不破坏现有流程？

- [ ] 跑 `python scripts/simulate.py` 通过
- [ ] 跑 `python -m doctest scripts/calculator.py -v` 全过
- [ ] 跑 `python -m doctest scripts/holidays.py -v` 全过
- [ ] 跑 `python -m doctest scripts/extract_effort.py -v` 全过
- [ ] 实跑 `orchestrator.py --dry-run-only` 在自己公司环境闭环
- [ ] 改动了 selectors → 跑了对应 `scripts/debug/` 里的 dump 脚本验证
- [ ] 没有引入新的硬编码个人化数据 / 公司内网 URL（`grep -r ysstech\|YOUR_COMPANY` 应该为空）

## 兼容性

- [ ] 这是 breaking change（改了 selectors.py 公开常量名 / 改了 SKILL.md frontmatter）
  - 如果是，CHANGELOG.md 要在 `[Unreleased]` 节加「Breaking」条目
- [ ] 兼容现有用户的配置和工作流

## 已脱敏

- [ ] PR 描述、测试输出、截图里**没有**：工号、真实姓名、内部 URL（除 example.com 占位）、单据号、项目代号
- [ ] commit message 里没有泄露公司信息

## 适配其他公司？

如果这个 PR 是为了让 skill 适配你公司而不是赢时胜：

- [ ] 你公司的 HR 系统：（金蝶 s-HR / 用友 / 钉钉 / 飞书 / 其他）
- [ ] 你公司的项目管理：（禅道 / Jira / Worktile / 其他）
- [ ] 你已经在 `selectors.py` / `submit_overtime.py` 里加了适配层（而不是直接覆盖原逻辑）
- [ ] 文档里说明了如何启用你的适配（比如 env var）
