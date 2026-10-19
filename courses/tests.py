from django.test import SimpleTestCase, TestCase
from django.contrib.auth.models import User

from .models import Course, Enrollment, Module, Progress, Subject, Video


class YouTubeEmbedUrlTests(SimpleTestCase):
    def test_watch_url_is_converted_to_embed_url(self):
        video = Video(video_url='https://www.youtube.com/watch?v=abc123')

        self.assertEqual(video.youtube_embed_url, 'https://www.youtube.com/embed/abc123')

    def test_short_link_is_converted_to_embed_url(self):
        video = Video(video_url='https://youtu.be/abc123')

        self.assertEqual(video.youtube_embed_url, 'https://www.youtube.com/embed/abc123')

    def test_existing_embed_url_and_query_are_preserved(self):
        url = 'https://www.youtube.com/embed/abc123?start=30'
        video = Video(video_url=url)

        self.assertEqual(video.youtube_embed_url, url)

    def test_non_youtube_url_is_preserved(self):
        url = 'https://player.vimeo.com/video/abc123'
        video = Video(video_url=url)

        self.assertEqual(video.youtube_embed_url, url)


class EnrollmentProgressTests(TestCase):
    def test_progress_percentage_preserves_fractional_progress(self):
        user = User.objects.create_user(username='student', password='password')
        subject = Subject.objects.create(title='Testing', slug='testing')
        course = Course.objects.create(
            owner=user,
            subject=subject,
            title='Large course',
            overview='A course with enough modules to expose integer truncation.',
        )
        enrollment = Enrollment.objects.create(user=user, course=course)
        modules = Module.objects.bulk_create([
            Module(course=course, title=f'Module {number}')
            for number in range(101)
        ])
        Progress.objects.create(user=user, module=modules[0], is_completed=True)

        self.assertEqual(enrollment.get_progress_percentage, 0.99)
