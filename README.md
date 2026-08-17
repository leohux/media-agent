# yt-dlp-agent

Leo Hu 的个人视频下载 Agent：把 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 包成 MCP 工具，给 WorkBuddy、Cursor、Claude Desktop、Qwen-Agent 等调用。

这不是官方 yt-dlp。内核来自 yt-dlp（Unlicense），本仓库在上面加了 Agent / MCP 层。

## 工具

| 工具 | 作用 |
|------|------|
| `extract_video_info` | 只解析标题、时长、格式，不下载 |
| `list_formats` | 列出可用清晰度 |
| `download_video` | 下载单个视频到指定目录 |

默认只接受 `http(s)` 链接，拒绝播放列表，下载目录可锁在白名单内。

站点覆盖与上游 yt-dlp 相同（B站、抖音、YouTube、小红书等一千多个提取器）。名单见 [`supportedsites.md`](supportedsites.md)。会员/DRM 内容经常下不了。

## 安装

```bash
git clone https://github.com/leohux/yt-dlp-agent.git
cd yt-dlp-agent
pip install -e ".[default,agent]"
```

需要 Python 3.10+。音频提取/合并建议安装 [ffmpeg](https://ffmpeg.org/)。

## MCP（WorkBuddy / Cursor / Claude）

```json
{
  "mcpServers": {
    "yt-dlp": {
      "command": "python",
      "args": ["-m", "yt_dlp.agent"],
      "env": {
        "YTDLP_AGENT_OUTPUT_DIR": "D:/downloads",
        "YTDLP_AGENT_ALLOWED_ROOT": "D:/downloads"
      }
    }
  }
}
```

- WorkBuddy：用户级配置 `~/.workbuddy/mcp.json`，或项目级 `.workbuddy/mcp.json`
- Cursor：`.cursor/mcp.json` 或 MCP 设置页
- 示例文件：[`mcp.example.json`](mcp.example.json)

千问网页版不能直接挂本地 MCP。把千问放在 WorkBuddy / Qwen-Agent 里当模型即可调用这些工具。

## 命令行调试

```bash
python -m yt_dlp.agent extract "https://www.youtube.com/watch?v=..."
python -m yt_dlp.agent formats "https://www.bilibili.com/video/..."
python -m yt_dlp.agent download "https://www.youtube.com/watch?v=..." --output-dir ./downloads --quality 720p
```

`quality`：`best`、`1080p`、`720p`、`480p`、`360p`、`audio_only`

原版 CLI 仍可用：

```bash
yt-dlp "https://www.youtube.com/watch?v=..."
```

不要对这个 fork 跑 `yt-dlp -U`，以免被官方包覆盖掉 Agent 层。

## 环境变量

| 变量 | 作用 |
|------|------|
| `YTDLP_AGENT_OUTPUT_DIR` | 默认下载目录 |
| `YTDLP_AGENT_ALLOWED_ROOT` | 下载路径必须落在此目录内 |

## 开发

```bash
python -m unittest test.test_agent_tools -v
```

## 致谢

下载内核来自 [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp)。本仓库仅增加 Agent/MCP 适配，并作为个人项目维护。

## 许可证

[Unlicense](LICENSE)（与上游 yt-dlp 相同）
