# 给同事的安装指南

> 这份指南面向想要使用 yss-overtime-submission skill 的同事。
> **创建人**：jiya1996
>
> 这个 skill 遵循 [agentskills.io](https://agentskills.io) 开放标准（Anthropic 牵头的 skill 格式），
> 所以可以装在 30+ 种 AI 客户端里。下面按场景给你推荐。

---

## ⚠️ 公共前置条件（不管选哪条路径都要）

1. **会用 Chrome**：装最新版 Google Chrome
2. **能装 Python**：Python 3.10+（[python.org](https://python.org) 下载）
3. **了解合规**：公司可能禁用 RPA/自动化操作 HR 系统。**用前请咨询你们 IT/HR**，哪怕是用自己账号操作。本 skill 实测过一次成功（2026-05-08），不代表长期安全。

---

## 🥇 路径 A：OpenClaw（推荐给非程序员）

**特点**：装好后通过**微信/QQ/Telegram 等渠道直接和 AI 对话**就能调用 skill。原生支持 Windows。

### 安装步骤

1. **装 OpenClaw**（Windows PowerShell 一行）：
   ```powershell
   iwr -useb https://openclaw.ai/install.ps1 | iex
   ```
   （或参考 https://docs.openclaw.ai/start/getting-started）

2. **装 Python 依赖**：
   ```powershell
   python -m pip install playwright chinese-calendar
   python -m playwright install chromium
   ```

3. **把 skill 放到 OpenClaw 的 skills 目录**（具体路径见 OpenClaw 文档，通常是 `~/.openclaw/skills/`）：
   把 `yss-overtime-submission` 整个文件夹复制过去。

4. **启动 debug Chrome**（参考 [chrome_setup.md](chrome_setup.md)）+ 登录禅道和 SHR。

5. **在微信/Telegram 里跟 OpenClaw bot 对话**：
   > 「帮我提上周加班，奋斗内容是 XXX」

   bot 会自动调用 skill 完成。

### 适合谁
- 不想装命令行工具的运营/PM/HR 同事
- 喜欢在微信里完成所有事的人

---

## 🥈 路径 B：Claude Code（推荐给程序员）

**特点**：Anthropic 官方 CLI，对 skill 支持最好。

### 安装步骤

1. **装 Claude Code**：参考 https://docs.anthropic.com/claude/docs/claude-code
2. **装 Python 依赖**（同上）
3. **把 skill 放到 `~/.claude/skills/`**
4. **启动 debug Chrome** + 登录
5. **在终端里跑 `claude`**，对它说：「帮我提上周加班」

### 适合谁
- 已经在用 Claude Code 的人
- 程序员

---

## 🥉 路径 C：纯命令行（不要 AI）

**特点**：不需要任何 AI 客户端，直接跑 Python 脚本。

### 安装步骤

1. **装 Python 3.10+ + 依赖**：
   ```bash
   pip install playwright chinese-calendar
   playwright install chromium
   ```

2. **解压 skill 包到任意目录**

3. **启动 debug Chrome** + 登录禅道/SHR

4. **每周提加班单**（一行命令）：
   ```bash
   # Windows（cmd 必须加 PYTHONIOENCODING=utf-8 否则中文崩）
   set PYTHONIOENCODING=utf-8
   python scripts\orchestrator.py --start 2026-MM-DD --end 2026-MM-DD --content "<你做的事>" --confirm

   # Mac / Linux
   PYTHONIOENCODING=utf-8 python scripts/orchestrator.py --start 2026-MM-DD --end 2026-MM-DD --content "<你做的事>" --confirm
   ```

### 适合谁
- 会用命令行
- 不想装 AI 客户端
- 公司禁止 AI 工具但允许 Python

### 缺点
- selector 漂移时（SHR/禅道 UI 改版）没 AI 帮忙 debug，要自己跑 `scripts/debug/` 里的脚本对照修
- 没有自然语言交互

---

## 🥈 其他路径（兼容客户端）

按 [agentskills.io](https://agentskills.io) 的客户端列表，下面这些**理论上都能装这个 skill**（具体目录看各自文档）：

| 客户端 | 特色 | skill 目录（参考）|
|---|---|---|
| **TRAE**（字节 IDE）| 中文好 + 国内访问稳 | TRAE 文档 |
| **Cursor** | 程序员主流 IDE | Cursor docs/skills |
| **VS Code Copilot** | 已有用户多 | VS Code agent-skills 文档 |
| **Goose**（Block 出品）| 开源 | block.github.io/goose |
| **nanobot**（HKUDS）| 多渠道含微信 | nanobot.wiki |
| **GitHub Copilot** | GitHub 集成 | docs.github.com agent-skills |

---

## 🚦 怎么选？

```
是否会命令行？
├─ 不会
│   └─ 公司允许装个人 AI 助手吗？
│       ├─ 允许 → 路径 A（OpenClaw，微信里聊就能用）
│       └─ 不允许 → 让同事帮忙提，或手填（30 秒）
└─ 会
    └─ 是否在用 IDE？
        ├─ Cursor/VS Code → 用 IDE 的 skill 支持
        ├─ Claude Code → 路径 B
        └─ 都不用 → 路径 C（纯 Python）
```

---

## 📝 通用配置（不管哪条路径）

每个用户**第一次跑前**要做的事：

1. **登录 debug Chrome**（按 [chrome_setup.md](chrome_setup.md)）—— 验证码和密码用户自己输
2. **打开禅道 + SHR 两个 tab**
3. **不要关 Chrome**——脚本通过 CDP 端口 9222 复用登录态

---

## 🆘 常见问题

| 问题 | 解决 |
|---|---|
| 「连不上 9222 端口」 | Chrome 没用 debug 模式启动，重新按 chrome_setup.md 做 |
| 「Selector 错位 / 抓不到表格」 | SHR 或禅道 UI 改版了，参考 [system_navigation.md](system_navigation.md) 末尾的「Selector 失效流程」+ 跑 `scripts/debug/` 里对应的 dump 脚本 |
| 「中文乱码 / cp936 错误」 | Windows 控制台编码问题，命令前加 `set PYTHONIOENCODING=utf-8`（cmd）或 `$env:PYTHONIOENCODING="utf-8"`（PowerShell）|
| 「节假日识别错误」 | 每年元旦后跑 `python -m pip install -U chinese-calendar` 升级节假日库 |
| 「公司说我用 RPA 不合规」 | 立即停用，跟 IT/HR 沟通后再决定 |

---

## 🤝 反馈

发现 selector 失效或 SHR 改版导致脚本无法工作？
- **如果你会改**：按 system_navigation.md 末尾的流程修 `scripts/selectors.py`，发回给jiya1996（创建人）合并
- **如果你不会改**：截图 + 描述发回，我们这边修

---

## 📎 一句话发给同事

> 「这是jiya1996做的提加班单 AI 工具，遵循 agentskills.io 标准。
> 看 references/installation_for_colleagues.md 选条路径装一下就能用，
> 微信里也能用（装 OpenClaw 那条路径）。」
