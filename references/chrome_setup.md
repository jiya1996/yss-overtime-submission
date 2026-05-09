# Chrome 调试模式启动指南

> **为什么需要这个**：Playwright 默认会启动一个全新的、无登录态的 Chrome。
> 但 SHR 和禅道都需要登录（且禅道有验证码），如果让 Playwright 重新登录会很麻烦。
> 解决方法：让 Playwright **连接到你已经手动登录好的 Chrome**，复用 session。
> 这需要 Chrome 启动时开一个调试端口。

---

## 一、关键概念（30 秒理解）

普通启动的 Chrome ≈ 上锁的房子，外人进不去。
带 `--remote-debugging-port` 启动的 Chrome ≈ 开着调试窗口的房子，Playwright 可以从那个窗口探进去操作。

**安全提示**：调试端口只监听 `127.0.0.1`（本机回环），外网访问不到。但同一台机器上的其他程序可以连。所以**别在公共/共享电脑上开调试模式**。

---

## 二、Windows 启动步骤

### 一次性配置（推荐：建一个专用快捷方式）

1. 关掉**所有** Chrome 窗口（包括后台进程，可在任务管理器确认 `chrome.exe` 没了）。
2. 桌面右键 → 新建 → 快捷方式，目标填：
   ```
   "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chrome-yss-debug"
   ```
   > `--user-data-dir` 指定一个**独立的 Chrome 配置目录**，避免污染你日常 Chrome 的书签和插件。第一次启动会是干净的 Chrome，登一次后续就记住了。
3. 命名为 `Chrome-YSS-Debug`，双击启动。
4. 在这个新 Chrome 里手动登录：
   - https://pm.example.com:8071 （禅道，过验证码 + 勾"记住密码"）
   - https://oa.example.com:5887/shr/dynamic.do?uipk=shr.perself.homepage&inFrame=true&blank=true （SHR）
5. **保持这两个 tab 不关**，下次只要双击快捷方式就会从这次状态继续。

### 验证调试端口生效

打开新浏览器访问 http://localhost:9222 ，能看到一个网页列表（你打开的所有 tab）说明成功。看到的就是 Playwright 看到的。

---

## 三、Mac 启动步骤

```bash
# 关掉所有 Chrome
killall "Google Chrome" 2>/dev/null

# 启动调试模式（用独立配置目录）
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
    --remote-debugging-port=9222 \
    --user-data-dir="$HOME/chrome-yss-debug" &
```

可以把这一行存成 `~/chrome-yss.sh`，加 `chmod +x`，以后每天 `./chrome-yss.sh` 启动。

---

## 四、Playwright 怎么连进去

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # 关键：用 connect_over_cdp 而不是 launch
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    
    # 复用第一个上下文（你已登录的那个）
    context = browser.contexts[0]
    
    # 找已经打开的 SHR tab，或新开一个
    page = next(
        (p for p in context.pages if "example.com" in p.url),
        None
    ) or context.new_page()
```

`scripts/connect_chrome.py` 已经把这段封装好了，直接 import 用即可。

---

## 五、常见问题

| 症状 | 原因 | 解决 |
|------|------|------|
| `connection refused localhost:9222` | Chrome 没用 debug 模式启动 | 关掉所有 Chrome，重新走步骤二/三 |
| 启动后 Chrome 是全新无登录的 | 用错了 `--user-data-dir` | 第一次必然是这样，登录一次以后就记住了 |
| 提示"Chrome 已在运行" | 后台还有 Chrome 进程 | Windows 任务管理器结束 `chrome.exe`；Mac 用 `killall` |
| Playwright 连上了但操作不了页面 | 页面在 iframe 里（SHR 经常这样）| 用 `page.frame_locator(...)` 不是 `page.locator(...)` |

---

## 六、合规提醒（再说一次）

- 调试端口 + 复用登录态 = 在你账号权限内做事，**没有提权**
- 但**自动操作 HR 系统**在很多公司是禁止的（哪怕是你自己账号）
- 用前问一下你们 IT/HR：「我能不能用脚本帮自己提交奋斗单？」
- 一旦被检测到（金蝶可能做埋点），后果你自己承担
