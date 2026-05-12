# yss-overtime-submission

> 一个用于赢时胜（YSS）员工**自动计算和提交加班单**的 AI Skill。
> 遵循 [agentskills.io](https://agentskills.io) 开放标准，可装在 Claude Code、OpenClaw、Cursor、Goose 等 30+ 兼容的 AI 客户端里。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![agentskills.io](https://img.shields.io/badge/agentskills.io-compatible-green.svg)](https://agentskills.io)

## 它能做什么

- 🕐 从禅道 OA 抓打卡数据
- 📅 按公司规则（工作日 19:00 后 / 节假日打卡到打卡 + 午晚餐扣除）自动算加班时长
- 🇨🇳 用 `chinese-calendar` 库正确识别中国大陆**法定假日和调休补班**
- 📋 跟金蝶 s-HR Cloud 已提交奋斗单做差集，**避免重复提交**
- 💡 从禅道工时确认页拉当天任务作为奋斗内容候选
- ✂️ 单日超过 8h 时自动按开始时间拆分多条，并分批提交
- 🤖 通过 Playwright 半自动填表 + 提交（必须 `--confirm` 才真正提交，全程人在环）

## 快速开始（5 分钟）

### 1. 安装依赖

```bash
git clone https://github.com/jiya1996/yss-overtime-submission.git
cd yss-overtime-submission
pip install -r requirements.txt
playwright install chromium
```

### 2. 配置你公司的域名

编辑 `scripts/selectors.py` 顶部两个常量，或用环境变量：

```bash
# Windows PowerShell
$env:YSS_ZENTAO_HOST = "pm.yourcompany.com:8071"
$env:YSS_SHR_HOST = "oa.yourcompany.com:5887"

# Mac / Linux
export YSS_ZENTAO_HOST=pm.yourcompany.com:8071
export YSS_SHR_HOST=oa.yourcompany.com:5887
```

### 3. 启动 debug 模式 Chrome + 登录

按 [`references/chrome_setup.md`](references/chrome_setup.md) 启动带 `--remote-debugging-port=9222` 的 Chrome，手动登录禅道和 SHR。

### 4. 跑

```bash
PYTHONIOENCODING=utf-8 python scripts/orchestrator.py \
    --start 2026-01-01 --end 2026-01-07 \
    --content "<你这周做的事>" \
    --dry-run-only      # 先 dry-run 看看抓到啥

# 确认无误后去掉 --dry-run-only 加 --confirm
```

详细使用流程见 [`SKILL.md`](SKILL.md)。

## 装到 AI 客户端里

### Claude Code（推荐给程序员）

```bash
git clone https://github.com/jiya1996/yss-overtime-submission.git ~/.claude/skills/yss-overtime-submission
```

然后跟 Claude 说「帮我提上周加班」自动调用。

### OpenClaw（推荐给非程序员）

```powershell
# Windows
iwr -useb https://openclaw.ai/install.ps1 | iex
```

把 skill 复制到 OpenClaw 的 skills 目录，之后**在微信里跟 bot 对话就能调用**。

### 其他兼容客户端

Cursor / VS Code Copilot / Goose / nanobot / TRAE / GitHub Copilot 等都支持，详见 [`references/installation_for_colleagues.md`](references/installation_for_colleagues.md)。

## 项目结构

```
yss-overtime-submission/
├── SKILL.md                     # skill 主入口，含 frontmatter
├── README.md                    # 本文件（GitHub 主页）
├── LICENSE                      # MIT
├── requirements.txt             # playwright + chinese-calendar
├── references/                  # 文档
│   ├── calculation_rules.md         # 加班时长计算规则
│   ├── chrome_setup.md              # Chrome debug 模式启动
│   ├── system_navigation.md         # 真实 URL + selector 对照表
│   └── installation_for_colleagues.md  # 4 种安装路径
└── scripts/                     # 核心代码
    ├── calculator.py                # 时长计算（带 doctest）
    ├── holidays.py                  # chinese-calendar 包装
    ├── selectors.py                 # 所有 selector 集中管理
    ├── connect_chrome.py            # CDP 连接
    ├── extract_attendance.py        # 抓禅道打卡
    ├── extract_submitted.py         # 抓 SHR 已提交
    ├── extract_effort.py            # 抓禅道工时（奋斗内容候选）
    ├── submit_overtime.py           # 提交加班单
    ├── orchestrator.py              # 总入口
    ├── simulate.py                  # 离线模拟（不连浏览器）
    └── debug/                       # selector 漂移时复用的 dump 脚本
```

## ⚠️ 风险声明

1. **公司可能禁用 RPA / 自动化操作 HR 系统**——使用前请咨询你们 IT/HR，**自行评估合规风险**
2. **Selector 会随 UI 改版漂移**——失效时跑 `scripts/debug/` 里的 dump 脚本对照修复
3. **节假日库每年要更新**：每年元旦后跑 `pip install -U chinese-calendar`
4. **永远不要全自动提交**：`submit_overtime.py` 必须传 `--confirm` 才提交

## 适配其他公司

这个 skill 默认适配**金蝶 s-HR Cloud + 禅道 OA** 的标准版。如果你公司用同一套系统：
- 改 `scripts/selectors.py` 顶部两个 host 常量即可
- selector 大概率通用（金蝶/禅道是私有部署但 UI 模板一致）

如果你公司用其他 HR 系统（钉钉、飞书审批、用友等）：需要重写 `submit_overtime.py` 和部分 selectors。可以参考本仓库的实现思路。

## 贡献

发现 bug / selector 失效 / 适配新公司？欢迎提 issue 或 PR：
- 描述你公司用的 SHR / 禅道版本
- 附上 dump 脚本输出的差异

## 许可

MIT License — 详见 [LICENSE](LICENSE)。
