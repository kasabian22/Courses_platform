import mimetypes
import re
from datetime import timezone
from email.utils import formatdate, parsedate_to_datetime
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse
from django.views.decorators.http import require_http_methods


class LimitedFile:
    def __init__(self, file, length):
        self.file = file
        self.name = file.name
        self.remaining = length

    def read(self, size=-1):
        if self.remaining <= 0:
            return b''
        if size is None or size < 0 or size > self.remaining:
            size = self.remaining
        data = self.file.read(size)
        self.remaining -= len(data)
        return data

    def close(self):
        self.file.close()


def _if_range_matches(value, modified_at):
    try:
        date = parsedate_to_datetime(value)
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        return int(modified_at) <= int(date.timestamp())
    except (TypeError, ValueError, OverflowError):
        return False


@require_http_methods(['GET', 'HEAD'])
def serve_media(request, media_path):
    media_root = Path(settings.MEDIA_ROOT).resolve()
    file_path = (media_root / media_path).resolve()
    if not file_path.is_relative_to(media_root) or not file_path.is_file():
        raise Http404

    file_stat = file_path.stat()
    file_size = file_stat.st_size
    modified_at = file_stat.st_mtime
    content_type = mimetypes.guess_type(file_path.name)[0] or 'application/octet-stream'
    range_header = request.headers.get('Range')
    if_range = request.headers.get('If-Range')
    if range_header and if_range and not _if_range_matches(if_range, modified_at):
        range_header = None

    range_match = re.fullmatch(r'bytes=(\d*)-(\d*)', range_header or '')
    if range_header and ',' not in range_header and range_match:
        first, last = range_match.groups()
        if not first and not last:
            range_match = None
        elif not file_size:
            return HttpResponse(status=416, headers={
                'Content-Range': 'bytes */0',
                'Accept-Ranges': 'bytes',
            })
        else:
            if first:
                start = int(first)
                end = min(int(last), file_size - 1) if last else file_size - 1
            else:
                suffix_length = int(last)
                if suffix_length == 0:
                    return HttpResponse(status=416, headers={
                        'Content-Range': f'bytes */{file_size}',
                        'Accept-Ranges': 'bytes',
                    })
                start = max(0, file_size - suffix_length)
                end = file_size - 1
            if first and (start >= file_size or start > end):
                return HttpResponse(status=416, headers={
                    'Content-Range': f'bytes */{file_size}',
                    'Accept-Ranges': 'bytes',
                })
            range_match = (start, end)
    elif range_header and ',' not in range_header and re.fullmatch(r'bytes=\d*-\d*', range_header):
        return HttpResponse(status=416, headers={
            'Content-Range': f'bytes */{file_size}',
            'Accept-Ranges': 'bytes',
        })
    else:
        range_match = None

    if range_match:
        start, end = range_match
        length = end - start + 1
        file = file_path.open('rb')
        file.seek(start)
        if request.method == 'HEAD':
            file.close()
            response = HttpResponse(status=206, content_type=content_type)
        else:
            response = FileResponse(
                LimitedFile(file, length),
                status=206,
                content_type=content_type,
            )
        response['Content-Length'] = str(length)
        response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
    else:
        if request.method == 'HEAD':
            response = HttpResponse(content_type=content_type)
            response['Content-Length'] = str(file_size)
        else:
            response = FileResponse(file_path.open('rb'), content_type=content_type)

    response['Accept-Ranges'] = 'bytes'
    response['Last-Modified'] = formatdate(modified_at, usegmt=True)
    return response
