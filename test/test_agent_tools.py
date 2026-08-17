#!/usr/bin/env python3

# Allow direct execution
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from yt_dlp.agent.tools import (
    QUALITY_FORMATS,
    AgentToolError,
    _format_selector,
    _parse_cookies_from_browser,
    _resolve_output_dir,
    _validate_url,
    download_video,
    extract_video_info,
    list_formats,
)

SAMPLE_URL = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
SAMPLE_INFO = {
    '_type': 'video',
    'id': 'dQw4w9WgXcQ',
    'title': 'Rick Astley - Never Gonna Give You Up',
    'duration': 213,
    'uploader': 'RickAstleyVEVO',
    'webpage_url': SAMPLE_URL,
    'ext': 'mp4',
    'thumbnail': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg',
    'description': 'A' * 600,
    'extractor_key': 'Youtube',
    'formats': [
        {'format_id': '18', 'ext': 'mp4', 'height': 360, 'vcodec': 'avc1', 'acodec': 'mp4a'},
        {'format_id': '22', 'ext': 'mp4', 'height': 720, 'vcodec': 'avc1', 'acodec': 'mp4a'},
    ],
}


class TestAgentValidation(unittest.TestCase):
    def test_url_required(self):
        with self.assertRaises(AgentToolError):
            _validate_url('')
        with self.assertRaises(AgentToolError):
            _validate_url(None)

    def test_url_rejects_non_http(self):
        with self.assertRaises(AgentToolError):
            _validate_url('file:///etc/passwd')
        with self.assertRaises(AgentToolError):
            _validate_url('javascript:alert(1)')
        with self.assertRaises(AgentToolError):
            _validate_url('not a url')

    def test_url_accepts_https(self):
        self.assertEqual(_validate_url(f'  {SAMPLE_URL}  '), SAMPLE_URL)

    def test_quality_aliases(self):
        self.assertEqual(_format_selector('720p', merge=True), QUALITY_FORMATS['720p'])
        self.assertEqual(_format_selector('BEST', merge=True), QUALITY_FORMATS['best'])
        self.assertEqual(_format_selector('best', audio_only=True, merge=True), QUALITY_FORMATS['audio_only'])
        self.assertEqual(_format_selector('360p', merge=False), 'b[height<=360]/b')
        with self.assertRaises(AgentToolError):
            _format_selector('4k')

    def test_output_dir_must_stay_inside_root(self):
        with tempfile.TemporaryDirectory() as root:
            allowed = os.path.join(root, 'downloads')
            os.makedirs(allowed)
            resolved = _resolve_output_dir(os.path.join(allowed, 'today'), allowed_root=allowed)
            self.assertTrue(resolved.startswith(os.path.realpath(allowed)))
            with self.assertRaises(AgentToolError):
                _resolve_output_dir(os.path.join(root, 'outside'), allowed_root=allowed)


class TestCookiesFromBrowser(unittest.TestCase):
    def test_parse_chrome(self):
        parsed = _parse_cookies_from_browser('chrome')
        self.assertEqual(parsed[0], 'chrome')

    def test_parse_profile(self):
        parsed = _parse_cookies_from_browser('chrome:Profile 1')
        self.assertEqual(parsed[0], 'chrome')
        self.assertEqual(parsed[1], 'Profile 1')

    def test_parse_rejects_unknown_browser(self):
        with self.assertRaises(AgentToolError):
            _parse_cookies_from_browser('netscape')

    def test_extract_rejects_missing_cookiefile(self):
        result = extract_video_info(
            SAMPLE_URL, cookiefile='C:/definitely-missing-cookies.txt')
        self.assertFalse(result['ok'])
        self.assertIn('cookie file not found', result['error'])

    def test_extract_passes_browser_cookies(self):
        captured = {}

        def fake_run(params, url, *, download):
            captured['params'] = params
            return SAMPLE_INFO.copy()

        with patch('yt_dlp.agent.tools._run_ydl', side_effect=fake_run):
            result = extract_video_info(SAMPLE_URL, cookies_from_browser='edge')
        self.assertTrue(result['ok'])
        self.assertEqual(captured['params']['cookiesfrombrowser'][0], 'edge')


class TestAgentTools(unittest.TestCase):
    def test_extract_rejects_bad_url_without_ydl(self):
        result = extract_video_info('ftp://example.com/a')
        self.assertFalse(result['ok'])
        self.assertIn('http', result['error'])

    def test_extract_summarizes_info(self):
        with patch('yt_dlp.agent.tools._run_ydl', return_value=SAMPLE_INFO.copy()):
            result = extract_video_info(SAMPLE_URL)

        self.assertTrue(result['ok'])
        self.assertEqual(result['id'], 'dQw4w9WgXcQ')
        self.assertEqual(result['title'], SAMPLE_INFO['title'])
        self.assertEqual(result['duration'], 213)
        self.assertTrue(result['description'].endswith('…'))
        self.assertEqual(len(result['formats']), 2)
        self.assertIsNone(result['error'])

    def test_extract_rejects_playlist(self):
        playlist = {'_type': 'playlist', 'title': 'Uploads', 'playlist_count': 12, 'entries': []}
        with patch('yt_dlp.agent.tools._run_ydl', return_value=playlist):
            result = extract_video_info(SAMPLE_URL)
        self.assertFalse(result['ok'])
        self.assertEqual(result['n_entries'], 12)
        self.assertIn('playlist', result['error'].lower())

    def test_list_formats(self):
        with patch('yt_dlp.agent.tools._run_ydl', return_value=SAMPLE_INFO.copy()):
            result = list_formats(SAMPLE_URL)
        self.assertTrue(result['ok'])
        self.assertEqual(result['formats'][1]['format_id'], '22')

    def test_download_writes_structured_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_file = os.path.join(tmp, 'video [id].mp4')
            with open(fake_file, 'wb') as f:
                f.write(b'abc')
            info = SAMPLE_INFO.copy()
            info['requested_downloads'] = [{'filepath': fake_file}]
            with patch('yt_dlp.agent.tools._run_ydl', return_value=info):
                result = download_video(SAMPLE_URL, output_dir=tmp, quality='720p')

        self.assertTrue(result['ok'])
        self.assertEqual(result['filepath'], os.path.realpath(fake_file))
        self.assertEqual(result['filesize'], 3)
        self.assertEqual(result['quality'], '720p')

    def test_download_invalid_quality(self):
        result = download_video(SAMPLE_URL, quality='tiny')
        self.assertFalse(result['ok'])
        self.assertIn('quality', result['error'])

    def test_download_rejects_string_false_audio_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_file = os.path.join(tmp, 'video [id].mp4')
            with open(fake_file, 'wb') as f:
                f.write(b'abc')
            info = SAMPLE_INFO.copy()
            info['requested_downloads'] = [{'filepath': fake_file}]
            with patch('yt_dlp.agent.tools._run_ydl', return_value=info), \
                    patch('yt_dlp.agent.tools._ffmpeg_available', return_value=False):
                result = download_video(
                    SAMPLE_URL, output_dir=tmp, quality='best', audio_only='false')
        self.assertTrue(result['ok'])
        self.assertEqual(result['quality'], 'best')

    def test_download_missing_file_is_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch('yt_dlp.agent.tools._run_ydl', return_value=SAMPLE_INFO.copy()):
                result = download_video(SAMPLE_URL, output_dir=tmp, quality='360p')
        self.assertFalse(result['ok'])
        self.assertIn('output file was not found', result['error'])


class TestAgentCLI(unittest.TestCase):
    def test_cli_extract(self):
        from io import StringIO

        from media_agent.__main__ import main
        buf = StringIO()
        with patch('yt_dlp.agent.tools._run_ydl', return_value=SAMPLE_INFO.copy()), \
                patch('sys.stdout', buf):
            code = main(['extract', SAMPLE_URL, '--no-formats'])
        self.assertEqual(code, 0)
        self.assertIn('"ok": true', buf.getvalue())


class TestMCPServer(unittest.TestCase):
    def test_create_server_registers_tools(self):
        try:
            from yt_dlp.agent.mcp_server import create_server
            server = create_server()
        except SystemExit:
            self.skipTest('mcp is not installed')

        mgr = getattr(server, '_tool_manager', None)
        self.assertIsNotNone(mgr)
        tools = mgr.list_tools()
        names = {getattr(t, 'name', None) for t in tools}
        self.assertEqual(
            names,
            {'extract_video_info', 'list_formats', 'download_video'})


if __name__ == '__main__':
    unittest.main()
