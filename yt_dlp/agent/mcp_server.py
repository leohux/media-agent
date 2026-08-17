"""MCP stdio server for media-agent."""

from . import tools as agent_tools


def _load_server_class():
    try:
        from mcp.server.fastmcp import FastMCP
        return FastMCP
    except ImportError:
        pass
    try:
        from mcp.server.mcpserver import MCPServer
        return MCPServer
    except ImportError:
        pass
    try:
        from mcp.server import MCPServer
        return MCPServer
    except ImportError as e:
        raise SystemExit(
            'The MCP extra is required. Install with: pip install "media-agent[agent]" '
            'or: pip install mcp'
        ) from e


def create_server():
    Server = _load_server_class()
    try:
        mcp = Server(
            'media-agent',
            instructions=(
                'Download or inspect online videos. '
                'Always call extract_video_info first when the user has not confirmed '
                'the title/duration. Never pass playlist URLs; use a single video URL. '
                'Only http(s) URLs are accepted.'
            ),
        )
    except TypeError:
        mcp = Server('media-agent')

    @mcp.tool(name='extract_video_info')
    def extract_video_info(url: str, include_formats: bool = True) -> dict:
        """Parse a video URL without downloading.

        Returns title, duration, uploader, and optionally available formats.
        Use this before download_video when the user has not confirmed what to fetch.
        """
        return agent_tools.extract_video_info(url, include_formats=include_formats)

    @mcp.tool(name='list_formats')
    def list_formats(url: str) -> dict:
        """List available video/audio formats for a URL without downloading."""
        return agent_tools.list_formats(url)

    @mcp.tool(name='download_video')
    def download_video(
            url: str,
            output_dir: str | None = None,
            quality: str = 'best',
            audio_only: bool = False) -> dict:
        """Download a single video to output_dir.

        quality: best, 1080p, 720p, 480p, 360p, audio, or audio_only.
        Playlists are rejected. Returns filepath on success.
        """
        return agent_tools.download_video(
            url,
            output_dir=output_dir,
            quality=quality,
            audio_only=audio_only,
        )

    return mcp


def run_mcp():
    create_server().run(transport='stdio')
