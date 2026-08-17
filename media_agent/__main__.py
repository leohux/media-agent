#!/usr/bin/env python3
"""Run media-agent.

MCP (stdio, for WorkBuddy / Cursor / Claude / Qwen-Agent)::

    python -m media_agent
    media-agent

CLI::

    python -m media_agent extract https://example.com/watch?v=...
    python -m media_agent formats https://example.com/watch?v=...
    python -m media_agent download https://example.com/watch?v=... --output-dir ./downloads --quality 720p
"""

from yt_dlp.agent.__main__ import main

if __name__ == '__main__':
    raise SystemExit(main())
