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
                'Only http(s) URLs are accepted. '
                'Sites like Douyin may need cookies_from_browser="chrome" or "edge" '
                'after opening the site in that browser.'
            ),
        )
    except TypeError:
        mcp = Server('media-agent')

    @mcp.tool(name='extract_video_info')
    def extract_video_info(
            url: str,
            include_formats: bool = True,
            cookies_from_browser: str | None = None,
            cookiefile: str | None = None) -> dict:
        """Parse a video URL without downloading.

        Returns title, duration, uploader, and optionally available formats.
        For Douyin/TikTok, pass cookies_from_browser="chrome" or "edge".
        """
        return agent_tools.extract_video_info(
            url, include_formats=include_formats,
            cookies_from_browser=cookies_from_browser, cookiefile=cookiefile)

    @mcp.tool(name='list_formats')
    def list_formats(
            url: str,
            cookies_from_browser: str | None = None,
            cookiefile: str | None = None) -> dict:
        """List available video/audio formats for a URL without downloading."""
        return agent_tools.list_formats(
            url, cookies_from_browser=cookies_from_browser, cookiefile=cookiefile)

    @mcp.tool(name='download_video')
    def download_video(
            url: str,
            output_dir: str | None = None,
            quality: str = 'best',
            audio_only: bool = False,
            cookies_from_browser: str | None = None,
            cookiefile: str | None = None) -> dict:
        """Download a single video to output_dir.

        quality: best, 1080p, 720p, 480p, 360p, audio, or audio_only.
        Playlists are rejected. Returns filepath on success.
        For Douyin, pass cookies_from_browser="chrome" or "edge".
        """
        return agent_tools.download_video(
            url,
            output_dir=output_dir,
            quality=quality,
            audio_only=audio_only,
            cookies_from_browser=cookies_from_browser,
            cookiefile=cookiefile,
        )

    return mcp


def run_mcp():
    server = create_server()
    try:
        server.run(transport='stdio')
    except TypeError:
        server.run()
