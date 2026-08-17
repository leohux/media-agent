<!-- MANPAGE: BEGIN EXCLUDED SECTION -->
<div align="center">

<a href="https://github.com/leohux/media-agent">
  <img src=".github/banner.svg" alt="media-agent" width="820">
</a>

**MEDIA-AGENT**
<br>
<em>A MCP video-download agent for WorkBuddy, Cursor, and other hosts</em>

<br>

[![Release](https://img.shields.io/github/v/release/leohux/media-agent?color=brightgreen&label=Latest&style=for-the-badge)](https://github.com/leohux/media-agent/releases)
[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue?style=for-the-badge)](https://www.python.org/)
[![License: Unlicense](https://img.shields.io/badge/license-Unlicense-red?style=for-the-badge)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-stdio-5865F2?style=for-the-badge)](mcp.example.json)

</div>
<!-- MANPAGE: END EXCLUDED SECTION -->

media-agent 让 AI 智能体真正去下载视频：你在 WorkBuddy / Cursor / Claude Desktop 里丢一条链接，Agent 会先解析标题和时长，再把文件存到你指定的目录。

底层下载能力来自 [yt-dlp](https://github.com/yt-dlp/yt-dlp)（Unlicense）。**这不是官方 yt-dlp**，对外产品名是 media-agent。

<div align="center">
  <img src=".github/hero.png" alt="media-agent hero" width="760">
  <br>
  <img src=".github/architecture.svg" alt="Agent 调用 media-agent 的三个工具" width="820">
</div>

## 目录

- [它是什么](#它是什么)
- [安装](#安装)
    - [Release 包](#release-包)
    - [从源码](#从源码)
    - [依赖](#依赖)
- [接到 AI 工具](#接到-ai-工具mcp)
    - [WorkBuddy / Cursor / Claude](#workbuddy--cursor--claude)
    - [千问](#千问)
- [三个工具](#三个工具)
- [命令行](#命令行)
- [支持哪些网站](#支持哪些网站)
- [安全限制](#安全限制)
- [常见问题](#常见问题)
- [开发](#开发)
- [致谢与许可](#致谢与许可)

## 它是什么

一层专门给大模型调用的 **MCP / CLI 接口**。人不用记一长串下载参数；Agent 只看到三个固定工具，返回 JSON。

| 适合 | 不适合 |
|------|--------|
| WorkBuddy / Cursor 里说「把这个视频存到 D 盘」 | 网页版通义千问直接挂本地工具 |
| 命令行解析、下载**单条**链接 | 整份播放列表、整频道扒取 |
| B站 / 抖音 / YouTube / 小红书等公开视频 | 会员、DRM、付费课破解 |

## 安装

### Release 包

到 [Releases](https://github.com/leohux/media-agent/releases) 下载最新 wheel：

```bash
pip install media_agent-0.1.2-py3-none-any.whl
pip install mcp
```

### 从源码

```bash
git clone https://github.com/leohux/media-agent.git
cd media-agent
pip install -e ".[default,agent]"
```

自检：

```bash
python -m media_agent --help
python -m media_agent extract "https://www.youtube.com/watch?v=jNQXAC9IVRw"
```

`ok` 为 `true` 即解析成功。

### 依赖

- Python **≥ 3.10**
- 建议安装 [ffmpeg](https://ffmpeg.org/)（合并音视频 / 抽音频）。没装也能下，会自动改用单文件格式
- 给 Agent 用：`pip install mcp`

## 接到 AI 工具（MCP）

本项目是 **MCP stdio 服务**。谁能配自定义 MCP，谁就能用。完整示例见 [mcp.example.json](mcp.example.json)。

把 `python` 换成你机器上的解释器路径。

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

### WorkBuddy / Cursor / Claude

| 产品 | 配置位置 |
|------|----------|
| WorkBuddy | `~/.workbuddy/mcp.json` 或项目内 `.workbuddy/mcp.json` |
| Cursor | MCP 设置页，或 `.cursor/mcp.json` |
| Claude Desktop | `claude_desktop_config.json` |

配好后直接说：

> 解析这个视频，确认标题后再下到 D:/downloads，清晰度 720p。
> https://www.bilibili.com/video/BV...

### 千问

- **能**：把千问放进 WorkBuddy / Qwen-Agent 当模型
- **不能**：通义千问网页版、阿里云百炼远程 SSE（本项目是本地 stdio）

## 三个工具

Agent 只能调这三项，不会直接拼下载命令。

| 工具 | 作用 | 何时用 |
|------|------|--------|
| `extract_video_info` | 只解析，不下文件 | 先确认标题、时长、UP 主 |
| `list_formats` | 列出清晰度 | 用户指定了 720p / 只下音频 |
| `download_video` | 下载**一条**视频 | 用户明确要保存文件 |

**`download_video` 参数**

| 参数 | 说明 |
|------|------|
| `url` | 必须是 `http://` 或 `https://` 的单条链接 |
| `output_dir` | 保存目录，可省略 |
| `quality` | `best` / `1080p` / `720p` / `480p` / `360p` / `audio_only` |
| `audio_only` | `true` 时只下音频 |

解析成功时大致返回：

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

失败则 `ok` 为 `false`，原因在 `error` 里。

## 命令行

```bash
python -m media_agent extract "https://www.bilibili.com/video/BVxxxx"
python -m media_agent formats "https://www.youtube.com/watch?v=..."
python -m media_agent download "https://www.youtube.com/watch?v=..." --output-dir D:/downloads --quality 720p
python -m media_agent download "https://..." --output-dir D:/downloads --audio-only
python -m media_agent   # 启动 MCP，给 Agent 用
```

## 支持哪些网站

与上游内核相同，约一千多个提取器。常见：

- 国内：B站、抖音、小红书、微博、优酷、爱奇艺、腾讯视频、芒果 TV、西瓜视频、AcFun、央视网、网易云、QQ 音乐
- 国外：YouTube、TikTok、Twitter/X、Instagram、Facebook、Twitch、Vimeo

完整名单：[supportedsites.md](supportedsites.md)

网站改版后个别站点可能失效。快手没有独立提取器。会员内容经常下不了。

## 安全限制

| 限制 | 行为 |
|------|------|
| 协议 | 只接受 `http` / `https` |
| 播放列表 | 拒绝，请传单条视频链接 |
| 目录 | `MEDIA_AGENT_ALLOWED_ROOT` 之内才能写 |
| 覆盖 | 默认不覆盖已有文件 |

| 环境变量 | 作用 |
|----------|------|
| `MEDIA_AGENT_OUTPUT_DIR` | 默认保存目录 |
| `MEDIA_AGENT_ALLOWED_ROOT` | 路径白名单根目录 |

## 常见问题

**WorkBuddy 配了但不调用？**  
确认 `command` 能执行 `python -m media_agent --help`，并且已安装 `mcp`。

**解析成功，YouTube 下载 403？**  
站点风控常见。可换其他平台或直链；当前 Agent 接口尚未暴露 cookie。

**提示要 ffmpeg？**  
没装也会下（单文件格式）。要高清画质+音轨合并，请安装 ffmpeg。

**能下播放列表吗？**  
不能。打开列表里的单集再传链接。

**和 yt-dlp 什么关系？**  
内核在 `yt_dlp/`，产品名是 media-agent。不要对这个仓库跑上游自动更新。

## 开发

```
media_agent/          对外入口：python -m media_agent
yt_dlp/agent/         三个工具 + MCP 服务
yt_dlp/               下载内核
test/test_agent_tools.py
mcp.example.json
.github/banner.svg
.github/hero.png
.github/architecture.svg
```

```bash
python -m unittest test.test_agent_tools -v
```

Agent / MCP / 文档问题请在 **本仓库** 开 Issue。网站解析坏了请到 [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp)。

## 致谢与许可

下载能力来自 [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp)，与官方无隶属关系。详见 [NOTICE](NOTICE)。

许可证：[Unlicense](LICENSE)
