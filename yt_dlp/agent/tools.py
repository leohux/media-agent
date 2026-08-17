import os
from urllib.parse import urlparse

from ..YoutubeDL import YoutubeDL
from ..utils import DownloadError, ExtractorError, int_or_none


QUALITY_FORMATS = {
    'best': 'bv*+ba/b',
    '1080p': 'bv*[height<=1080]+ba/b[height<=1080]/b',
    '720p': 'bv*[height<=720]+ba/b[height<=720]/b',
    '480p': 'bv*[height<=480]+ba/b[height<=480]/b',
    '360p': 'bv*[height<=360]+ba/b[height<=360]/b',
    'audio': 'bestaudio/best',
    'audio_only': 'bestaudio/best',
}

_ALLOWED_URL_SCHEMES = ('http', 'https')
_DESCRIPTION_LIMIT = 500
_FORMATS_LIMIT = 40
_DEFAULT_OUTPUT_DIRNAME = 'downloads'


class AgentToolError(ValueError):
    """Invalid agent-tool input (URL, quality, output path, ...)."""


class _QuietLogger:
    def debug(self, msg):
        pass

    def info(self, msg):
        pass

    def warning(self, msg, *, once=False):
        pass

    def error(self, msg, *, is_error=True):
        pass

    def stdout(self, msg):
        pass

    def stderr(self, msg):
        pass


def _fail(error, **extra):
    result = {'ok': False, 'error': str(error)}
    result.update(extra)
    return result


def _ok(**fields):
    result = {'ok': True, 'error': None}
    result.update(fields)
    return result


def _validate_url(url):
    if not isinstance(url, str) or not url.strip():
        raise AgentToolError('url is required')
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme.lower() not in _ALLOWED_URL_SCHEMES or not parsed.netloc:
        raise AgentToolError('Only http(s) URLs are allowed')
    return url


def _resolve_output_dir(output_dir=None, allowed_root=None):
    if not output_dir:
        output_dir = os.environ.get('YTDLP_AGENT_OUTPUT_DIR') or os.path.join(
            os.getcwd(), _DEFAULT_OUTPUT_DIRNAME)
    if not allowed_root:
        allowed_root = os.environ.get('YTDLP_AGENT_ALLOWED_ROOT')

    path = os.path.realpath(os.path.abspath(os.path.expanduser(output_dir)))
    if allowed_root:
        root = os.path.realpath(os.path.abspath(os.path.expanduser(allowed_root)))
        try:
            common = os.path.commonpath([path, root])
        except ValueError:
            raise AgentToolError(f'output_dir must be inside {root}')
        if os.path.normcase(common) != os.path.normcase(root):
            raise AgentToolError(f'output_dir must be inside {root}')

    os.makedirs(path, exist_ok=True)
    return path


def _format_selector(quality, audio_only=False):
    if audio_only:
        return QUALITY_FORMATS['audio_only']
    if not quality:
        quality = 'best'
    if not isinstance(quality, str):
        raise AgentToolError('quality must be a string')
    key = quality.strip().lower()
    if key in QUALITY_FORMATS:
        return QUALITY_FORMATS[key]
    raise AgentToolError(
        'quality must be one of: ' + ', '.join(QUALITY_FORMATS))


def _compact_formats(info):
    formats = []
    for fmt in info.get('formats') or []:
        if not isinstance(fmt, dict):
            continue
        formats.append({
            'format_id': fmt.get('format_id'),
            'ext': fmt.get('ext'),
            'resolution': fmt.get('resolution'),
            'height': int_or_none(fmt.get('height')),
            'fps': int_or_none(fmt.get('fps')),
            'vcodec': fmt.get('vcodec'),
            'acodec': fmt.get('acodec'),
            'filesize': int_or_none(fmt.get('filesize') or fmt.get('filesize_approx')),
            'tbr': fmt.get('tbr'),
        })
        if len(formats) >= _FORMATS_LIMIT:
            break
    return formats


def _filepaths(info):
    paths = []
    for item in info.get('requested_downloads') or []:
        if not isinstance(item, dict):
            continue
        path = item.get('filepath') or item.get('_filename') or item.get('filename')
        if path:
            paths.append(path)
    if not paths:
        path = info.get('filepath') or info.get('_filename') or info.get('filename')
        if path:
            paths.append(path)
    return paths


def _summarize_info(info, *, include_formats=False):
    description = info.get('description')
    if isinstance(description, str) and len(description) > _DESCRIPTION_LIMIT:
        description = description[:_DESCRIPTION_LIMIT] + '…'

    summary = {
        'id': info.get('id'),
        'title': info.get('title'),
        'duration': info.get('duration'),
        'uploader': info.get('uploader') or info.get('channel'),
        'webpage_url': info.get('webpage_url') or info.get('original_url'),
        'ext': info.get('ext'),
        'thumbnail': info.get('thumbnail'),
        'description': description,
        'extractor': info.get('extractor_key') or info.get('extractor'),
    }
    if include_formats:
        summary['formats'] = _compact_formats(info)
    return summary


def _base_params(*, quiet=True):
    return {
        'quiet': quiet,
        'no_warnings': True,
        'noprogress': True,
        'noplaylist': True,
        'ignoreerrors': False,
        'retries': 3,
        'fragment_retries': 3,
        'socket_timeout': 30,
        'restrictfilenames': True,
        'windowsfilenames': True,
        'logger': _QuietLogger(),
    }


def _run_ydl(params, url, *, download):
    with YoutubeDL(params) as ydl:
        return ydl.extract_info(url, download=download)


def _extract_or_error(url, params, *, download):
    try:
        info = _run_ydl(params, url, download=download)
    except (DownloadError, ExtractorError, OSError) as e:
        return _fail(e)
    except Exception as e:
        return _fail(e)

    if not info:
        return _fail('No information could be extracted from this URL')

    if info.get('_type') == 'playlist':
        n_entries = info.get('playlist_count')
        if n_entries is None:
            entries = info.get('entries') or []
            n_entries = len(list(entries)) if not isinstance(entries, list) else len(entries)
        return _fail(
            'URL is a playlist. Pass a single video URL instead.',
            playlist_title=info.get('title'),
            n_entries=n_entries,
        )

    return info


def extract_video_info(url, include_formats=True):
    """Parse a video URL without downloading the media file.

    Returns a JSON-serializable dict with title, duration, formats, etc.
    """
    try:
        url = _validate_url(url)
    except AgentToolError as e:
        return _fail(e)

    params = _base_params()
    params['skip_download'] = True
    info = _extract_or_error(url, params, download=False)
    if isinstance(info, dict) and info.get('ok') is False:
        return info
    return _ok(**_summarize_info(info, include_formats=include_formats))


def list_formats(url):
    """List available media formats for a video URL without downloading."""
    result = extract_video_info(url, include_formats=True)
    if not result.get('ok'):
        return result
    return _ok(
        id=result.get('id'),
        title=result.get('title'),
        formats=result.get('formats') or [],
    )


def download_video(
        url,
        output_dir=None,
        quality='best',
        audio_only=False,
        allowed_root=None):
    """Download a single video (or audio-only) to ``output_dir``.

    Playlists are rejected. The output path must stay inside ``allowed_root``
    when that is set (or ``YTDLP_AGENT_ALLOWED_ROOT``).
    """
    try:
        url = _validate_url(url)
        fmt = _format_selector(quality, audio_only=audio_only)
        out_dir = _resolve_output_dir(output_dir, allowed_root=allowed_root)
    except AgentToolError as e:
        return _fail(e)

    params = _base_params()
    params.update({
        'format': fmt,
        'outtmpl': '%(title)s [%(id)s].%(ext)s',
        'overwrites': False,
        'max_downloads': 1,
        'paths': {'home': out_dir},
    })
    if audio_only or fmt == QUALITY_FORMATS['audio_only']:
        params['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
            'preferredquality': '0',
        }]

    info = _extract_or_error(url, params, download=True)
    if isinstance(info, dict) and info.get('ok') is False:
        return info

    filepaths = [os.path.realpath(p) for p in _filepaths(info)]
    existing = [p for p in filepaths if os.path.isfile(p)]
    filepath = existing[0] if existing else (filepaths[0] if filepaths else None)
    filesize = os.path.getsize(filepath) if filepath and os.path.isfile(filepath) else None

    summary = _summarize_info(info, include_formats=False)
    return _ok(
        **summary,
        filepath=filepath,
        filesize=filesize,
        output_dir=out_dir,
        quality=quality if not audio_only else 'audio_only',
    )
