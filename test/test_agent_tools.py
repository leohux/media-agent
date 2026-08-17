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
        self.assertEqual(_format_selector('720p'), QUALITY_FORMATS['720p'])
        self.assertEqual(_format_selector('BEST'), QUALITY_FORMATS['best'])
        self.assertEqual(_format_selector('best', audio_only=True), QUALITY_FORMATS['audio_only'])
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


if __name__ == '__main__':
    unittest.main()
