# media-agent

给 AI Agent 用的**视频下载工具**。

你对 WorkBuddy、Cursor、Claude Desktop、Qwen-Agent 说「把这个链接的视频下下来」，它们会调用本项目的 MCP 工具：先解析标题和时长，再下载到你指定的目录。

当前版本：**0.1.1**  
仓库：https://github.com/leohux/media-agent  
Release：https://github.com/leohux/media-agent/releases/tag/v0.1.1

维护者：[Leo Hu](https://github.com/leohux)

---

## 它是什么

media-agent 是一层 **MCP / 命令行接口**，专门给大模型智能体调用。

底层下载能力来自 [yt-dlp](https://github.com/yt-dlp/yt-dlp)（Unlicense）。本仓库**不是** yt-dlp 官方项目，也不替代原版命令行。人继续可以用各种下载器；Agent 走这一套固定参数、返回 JSON 的工具。

```
WorkBuddy / Cursor / Claude / Qwen-Agent
        │  MCP（stdio）
        ▼
   media-agent  （3 个工具）
        │
        ▼
   下载内核（yt-dlp）
        │
        ▼
   B站 / 抖音 / YouTube / 小红书 / …
```

## 它不是什么

- 不是官方 yt-dlp，也不叫 yt-dlp
- 不是网页版「一键下载」App
- 不能破解会员、DRM、付费课
- 通义千问**网页聊天**不能直接挂这个本地工具（要把千问放进 WorkBuddy / Qwen-Agent 里当模型）

---

## 谁适合用

| 场景 | 是否适合 |
|------|----------|
| 在 WorkBuddy / Cursor 里让 Agent 下视频 | 适合 |
| 自己用命令行解析/下载单个链接 | 适合 |
| 批量扒整个播放列表、整频道 | 不适合（默认拒绝播放列表） |
| 下大会员 4K / 付费综艺 | 通常不行 |

---

## 三个工具

Agent 只看到这 3 个工具，不会直接拼一长串下载参数。

| 工具 | 做什么 | 什么时候用 |
|------|--------|------------|
| `extract_video_info` | 只解析，**不下载文件** | 先确认标题、时长、UP 主 |
| `list_formats` | 列出可用清晰度 | 用户指定了 720p / 只下音频 |
| `download_video` | 下载**一条**视频到目录 | 用户明确要保存文件 |

### 下载参数

| 参数 | 说明 |
|------|------|
| `url` | 必须是 `http://` 或 `https://` 的单条视频链接 |
| `output_dir` | 保存目录，可省略（用环境变量） |
| `quality` | `best` / `1080p` / `720p` / `480p` / `360p` / `audio_only` |
| `audio_only` | `true` 时只下音频 |

### 返回示例（解析）

```json
{
  "ok": true,
  "error": null,
  "id": "jNQXAC9IVRw",
  "title": "Me at the zoo",
  "duration": 19,
  "uploader": "jawed",
  "webpage_url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",
  "ext": "mp4",
  "extractor": "Youtube"
}
```

失败时 `ok` 为 `false`，`error` 里是原因，不会抛给 Agent 一堆堆栈。

---

## 支持哪些网站

和上游下载内核相同，大约一千多个提取器。常见包括：

- 国内：B站、抖音、小红书、微博、优酷、爱奇艺、腾讯视频、芒果 TV、西瓜视频、AcFun、央视网、网易云、QQ 音乐
- 国外：YouTube、TikTok、Twitter/X、Instagram、Facebook、Twitch、Vimeo

完整名单：[supportedsites.md](supportedsites.md)

说明：

- 网站改版后，个别站点可能突然失效
- 快手目前没有独立提取器，成功率低
- 要登录的内容可能需要 cookie（当前 Agent 层未暴露登录参数）

---

## 环境要求

- Python **3.10+**
- 建议安装 [ffmpeg](https://ffmpeg.org/)：用来合并音视频、抽音频。没装也能下，会自动改用「单文件」格式
- 给 Agent 用时再装：`pip install mcp`

---

## 安装

### 方式一：Release 包（推荐）

到 [Releases](https://github.com/leohux/media-agent/releases) 下载最新 wheel，例如 `0.1.1`：

```bash
pip install media_agent-0.1.1-py3-none-any.whl
pip install mcp
```

### 方式二：从源码

```bash
git clone https://github.com/leohux/media-agent.git
cd media-agent
pip install -e ".[default,agent]"
```

装好后先自检：

```bash
python -m media_agent --help
python -m media_agent extract "https://www.youtube.com/watch?v=jNQXAC9IVRw"
```

解析成功会打印 JSON，`ok` 为 `true`。

---

## 接到 AI 工具（MCP）

本项目对外是 **MCP stdio 服务**。谁能配自定义 MCP，谁就能用。

配置文件示例也在 [mcp.example.json](mcp.example.json)。

把 `python` 换成你机器上的实际路径（Windows 上常见是 `python.exe` 的完整路径）。

```json
{
  "mcpServers": {
    "media-agent": {
      "command": "python",
      "args": ["-m", "media_agent"],
      "env": {
        "MEDIA_AGENT_OUTPUT_DIR": "D:/downloads",
        "MEDIA_AGENT_ALLOWED_ROOT": "D:/downloads"
      }
    }
  }
}
```

| 产品 | 怎么配 | 能不能用 |
|------|--------|----------|
| **WorkBuddy** | `~/.workbuddy/mcp.json`，或项目里 `.workbuddy/mcp.json` | 能 |
| **Cursor** | MCP 设置页，或 `.cursor/mcp.json` | 能 |
| **Claude Desktop** | `claude_desktop_config.json` | 能 |
| **Qwen-Agent / 本地千问** | Agent 的 `mcpServers` | 能 |
| **千问网页版** | 无本地 MCP 入口 | 不能 |
| **阿里云百炼 MCP** | 要远程 SSE，本项目是本地 stdio | 不能直接用 |

配好后直接说：

> 解析这个视频，确认标题后再下到 D:/downloads，清晰度 720p。  
> https://www.bilibili.com/video/BV...

Agent 应先调 `extract_video_info`，再调 `download_video`。

---

## 命令行（不用 Agent 时）

```bash
# 只看信息
python -m media_agent extract "https://www.bilibili.com/video/BVxxxx"

# 看清晰度
python -m media_agent formats "https://www.youtube.com/watch?v=..."

# 下载
python -m media_agent download "https://www.youtube.com/watch?v=..." --output-dir D:/downloads --quality 720p

# 只下音频
python -m media_agent download "https://..." --output-dir D:/downloads --audio-only

# 启动 MCP（给 Agent 用，一般不要手动开）
python -m media_agent
```

---

## 安全限制

给模型调用时默认收紧，避免下错盘、下整个列表。

| 限制 | 行为 |
|------|------|
| 协议 | 只接受 `http` / `https`，拒绝 `file://` 等 |
| 播放列表 | 拒绝，请传单集/单条视频链接 |
| 下载目录 | 可设 `MEDIA_AGENT_ALLOWED_ROOT`，路径必须落在该目录内 |
| 覆盖 | 默认不覆盖已有文件 |

环境变量：

| 变量 | 作用 |
|------|------|
| `MEDIA_AGENT_OUTPUT_DIR` | 默认保存目录 |
| `MEDIA_AGENT_ALLOWED_ROOT` | 白名单根目录，越界会失败 |

---

## 常见问题

**Q：WorkBuddy 里配了但没调用？**  
确认 `command` 指向能跑 `python -m media_agent --help` 的解释器，并且已 `pip install mcp`。

**Q：解析成功，YouTube 下载 403？**  
站点风控常见。可换直链/其他平台试，或在本机安装 ffmpeg、必要时用浏览器 cookie（当前 Agent 接口尚未暴露 cookie 参数）。

**Q：提示要 ffmpeg？**  
0.1.1 起没装 ffmpeg 会自动改用单文件格式。要合并高清画质+音轨，仍建议安装 ffmpeg。

**Q：能下播放列表吗？**  
不能。请打开列表里的单条视频再传链接。

**Q：和 yt-dlp 什么关系？**  
内核代码在仓库的 `yt_dlp/` 目录，对外产品名是 media-agent。不要对这个 fork 跑上游的自动更新，以免盖掉 Agent 层。

---

## 项目结构

```
media_agent/          # 对外入口：python -m media_agent
yt_dlp/agent/         # 三个工具 + MCP 服务
yt_dlp/               # 下载内核（上游）
test/test_agent_tools.py
mcp.example.json      # MCP 配置示例
```

本地测试：

```bash
python -m unittest test.test_agent_tools -v
```

---

## 贡献

- Agent / MCP / 文档：在 **本仓库** 开 Issue 或 PR
- 某个网站解析坏了、要新增站点：请到上游 [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp)

---

## 致谢与许可

下载能力来自 [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp)。本项目与官方无隶属关系。详见 [NOTICE](NOTICE)。

许可证：[Unlicense](LICENSE)（与上游相同，可自由使用、修改、再分发）
