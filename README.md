# media-agent

Leo Hu 的个人视频下载 Agent。给 WorkBuddy、Cursor、Claude Desktop、Qwen-Agent 等调用，用来解析和下载在线视频。

下载内核来自 [yt-dlp](https://github.com/yt-dlp/yt-dlp)（Unlicense）。本仓库不是官方项目。

## 工具

| 工具 | 作用 |
|------|------|
| `extract_video_info` | 只解析标题、时长、格式，不下载 |
| `list_formats` | 列出可用清晰度 |
| `download_video` | 下载单个视频到指定目录 |

默认只接受 `http(s)` 链接，拒绝播放列表，下载目录可锁在白名单内。

支持的站点与上游内核相同（B站、抖音、YouTube、小红书等）。名单见 [`supportedsites.md`](supportedsites.md)。会员/DRM 内容经常下不了。

## 安装

```bash
git clone https://github.com/leohux/media-agent.git
cd media-agent
pip install -e ".[default,agent]"
```

需要 Python 3.10+。音频提取/合并建议安装 [ffmpeg](https://ffmpeg.org/)。

## MCP（WorkBuddy / Cursor / Claude）

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

- WorkBuddy：`~/.workbuddy/mcp.json` 或项目级 `.workbuddy/mcp.json`
- Cursor：MCP 设置页
- 示例：[`mcp.example.json`](mcp.example.json)

千问网页版不能直接挂本地 MCP。把千问放在 WorkBuddy / Qwen-Agent 里当模型即可。

## 命令行

```bash
python -m media_agent extract "https://www.youtube.com/watch?v=..."
python -m media_agent formats "https://www.bilibili.com/video/..."
python -m media_agent download "https://www.youtube.com/watch?v=..." --output-dir ./downloads --quality 720p
```

`quality`：`best`、`1080p`、`720p`、`480p`、`360p`、`audio_only`

不要对这个仓库跑上游的自动更新命令，以免覆盖 Agent 层。

## 环境变量

| 变量 | 作用 |
|------|------|
| `MEDIA_AGENT_OUTPUT_DIR` | 默认下载目录 |
| `MEDIA_AGENT_ALLOWED_ROOT` | 下载路径必须落在此目录内 |

## 开发

```bash
python -m unittest test.test_agent_tools -v
```

## 致谢

下载能力来自 [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp)。

## 许可证

[Unlicense](LICENSE)
