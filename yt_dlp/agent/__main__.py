#!/usr/bin/env python3
"""Run media-agent tools.

MCP (stdio)::

    python -m media_agent
    media-agent

CLI::

    python -m media_agent extract https://example.com/watch?v=...
    python -m media_agent formats https://example.com/watch?v=...
    python -m media_agent download https://example.com/watch?v=... --output-dir ./downloads --quality 720p
"""

import argparse
import json
import sys

from ..utils import write_string
from .tools import download_video, extract_video_info, list_formats


def _print_json(data):
    write_string(json.dumps(data, ensure_ascii=False, indent=2) + '\n', out=sys.stdout)
    return 0 if data.get('ok') else 1


def _build_parser():
    parser = argparse.ArgumentParser(
        prog='media-agent',
        description='media-agent (MCP server or JSON CLI)')
    sub = parser.add_subparsers(dest='command')

    sub.add_parser('mcp', help='Run the MCP stdio server (default)')

    p_extract = sub.add_parser('extract', help='Parse a video URL without downloading')
    p_extract.add_argument('url')
    p_extract.add_argument('--no-formats', action='store_true')
    p_extract.add_argument('--cookies-from-browser', default=None,
                           help='chrome, edge, firefox, ...')
    p_extract.add_argument('--cookies', dest='cookiefile', default=None)

    p_formats = sub.add_parser('formats', help='List formats for a video URL')
    p_formats.add_argument('url')
    p_formats.add_argument('--cookies-from-browser', default=None)
    p_formats.add_argument('--cookies', dest='cookiefile', default=None)

    p_download = sub.add_parser('download', help='Download a single video')
    p_download.add_argument('url')
    p_download.add_argument('--output-dir', default=None)
    p_download.add_argument('--quality', default='best')
    p_download.add_argument('--audio-only', action='store_true')
    p_download.add_argument('--cookies-from-browser', default=None)
    p_download.add_argument('--cookies', dest='cookiefile', default=None)
    return parser


def _cli(argv):
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command in (None, 'mcp'):
        from .mcp_server import run_mcp
        run_mcp()
        return 0
    if args.command == 'extract':
        return _print_json(extract_video_info(
            args.url, include_formats=not args.no_formats,
            cookies_from_browser=args.cookies_from_browser,
            cookiefile=args.cookiefile))
    if args.command == 'formats':
        return _print_json(list_formats(
            args.url,
            cookies_from_browser=args.cookies_from_browser,
            cookiefile=args.cookiefile))
    if args.command == 'download':
        return _print_json(download_video(
            args.url,
            output_dir=args.output_dir,
            quality=args.quality,
            audio_only=args.audio_only,
            cookies_from_browser=args.cookies_from_browser,
            cookiefile=args.cookiefile,
        ))
    parser.print_help()
    return 2


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    # Bare invocation is MCP stdio: python -m media_agent
    if not argv:
        from .mcp_server import run_mcp
        run_mcp()
        return 0
    return _cli(argv)


if __name__ == '__main__':
    raise SystemExit(main())
