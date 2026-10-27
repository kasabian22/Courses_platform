import tempfile
from pathlib import Path

from django.test import RequestFactory, SimpleTestCase, override_settings

from .media_views import serve_media


class ServeMediaRangeTests(SimpleTestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.media_root = Path(self.temp_dir.name)
        (self.media_root / 'sample.mp4').write_bytes(b'0123456789')
        self.factory = RequestFactory()

    def test_serves_requested_byte_range(self):
        with override_settings(MEDIA_ROOT=self.media_root):
            response = serve_media(
                self.factory.get('/media/sample.mp4', HTTP_RANGE='bytes=3-6'),
                'sample.mp4',
            )

        self.assertEqual(response.status_code, 206)
        self.assertEqual(response['Content-Range'], 'bytes 3-6/10')
        self.assertEqual(response['Content-Length'], '4')
        self.assertEqual(b''.join(response.streaming_content), b'3456')
        response.close()

    def test_serves_suffix_range(self):
        with override_settings(MEDIA_ROOT=self.media_root):
            response = serve_media(
                self.factory.get('/media/sample.mp4', HTTP_RANGE='bytes=-3'),
                'sample.mp4',
            )

        self.assertEqual(response.status_code, 206)
        self.assertEqual(response['Content-Range'], 'bytes 7-9/10')
        self.assertEqual(b''.join(response.streaming_content), b'789')
        response.close()

    def test_unsatisfiable_range_returns_416(self):
        with override_settings(MEDIA_ROOT=self.media_root):
            response = serve_media(
                self.factory.get('/media/sample.mp4', HTTP_RANGE='bytes=10-'),
                'sample.mp4',
            )

        self.assertEqual(response.status_code, 416)
        self.assertEqual(response['Content-Range'], 'bytes */10')

    def test_empty_range_is_ignored(self):
        with override_settings(MEDIA_ROOT=self.media_root):
            response = serve_media(
                self.factory.get('/media/sample.mp4', HTTP_RANGE='bytes=-'),
                'sample.mp4',
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'0123456789')
        response.close()

    def test_head_reports_file_size_without_streaming_body(self):
        with override_settings(MEDIA_ROOT=self.media_root):
            response = serve_media(
                self.factory.head('/media/sample.mp4'),
                'sample.mp4',
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Length'], '10')
        self.assertFalse(response.streaming)
