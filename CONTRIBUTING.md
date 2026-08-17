# 贡献说明

这是 **media-agent**，[Leo Hu](https://github.com/leohux) 的个人开源项目：把视频下载做成给 AI Agent 调用的 MCP 工具。

## 在这里提

- MCP 接不上、工具参数、返回 JSON、文档、安装包
- Agent 误下播放列表、路径越界等安全相关问题

请开 Issue，尽量带上：

1. 完整命令或 MCP 配置（可打码路径）
2. `python -m media_agent extract "链接"` 的 JSON 输出
3. Python 版本、操作系统

## 请到上游提

某个网站突然不能解析、要支持新站点：  
https://github.com/yt-dlp/yt-dlp

本仓库不接收「把内核改名叫别的」这类与 Agent 层无关的大重构，除非你先开 Issue 说清目的。
