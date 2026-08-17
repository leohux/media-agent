"""Agent-facing wrappers around yt-dlp.

These helpers expose a small, structured API for LLM tools / MCP servers.
They do not replace the CLI; they only wrap ``YoutubeDL``.
"""

from .tools import (
    AgentToolError,
    QUALITY_FORMATS,
    download_video,
    extract_video_info,
    list_formats,
)

__all__ = [
    'AgentToolError',
    'QUALITY_FORMATS',
    'download_video',
    'extract_video_info',
    'list_formats',
]
