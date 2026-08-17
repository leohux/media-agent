"""media-agent public entrypoint.

The download engine still lives in ``yt_dlp``; this package is the
product-facing CLI / MCP wrapper.
"""

from yt_dlp.agent import (
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
