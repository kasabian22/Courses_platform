import json
from django.test import SimpleTestCase, TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Course, Enrollment, Module, Progress, Subject, Video


def quill_content(text="Course overview"):
    return json.dumps({
        "delta": json.dumps({"ops": [{"insert": f"{text}\n"}]}),
        "html": f"<p>{text}</p>"
    })


class CourseTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="kasabian", password="password")
        self.subject = Subject.objects.create(
            title=Subject.Subjects.WEB_DEV,
            slug="web-development"
        )

        self.c1 = Course.objects.create(
            owner=self.user,
            subject=self.subject,
            title="Django | Orm System",
            slug="django-orm-system",
            overview=quill_content("Overview 1"),
            header="header",
            status=Course.Status.AVAILABLE,
        )

        self.c2 = Course.objects.create(
            owner=self.user,
            subject=self.subject,
            title="Django | Views System",
            slug="django-views-system",
            overview=quill_content("Overview 2"),
            header="header2",
            status=Course.Status.AVAILABLE,
        )

    def test_index(self):
        response1 = self.client.get(reverse('courses:course_detail', kwargs={'slug': 'django-orm-system'}))
        response2 = self.client.get(reverse('courses:course_detail', kwargs={'slug': 'django-views-system'}))
        response3 = self.client.get(reverse('courses:category_courses', kwargs={'subject_slug': 'web-development'}))

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response3.status_code, 200)
        self.assertEqual(len(response3.context["courses"]), 2)


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
        subject = Subject.objects.create(
            title=Subject.Subjects.OTHER,
            slug='other'
        )
        course = Course.objects.create(
            owner=user,
            subject=subject,
            title='Large course',
            overview=quill_content("A course with enough modules to expose integer truncation."),
        )
        enrollment = Enrollment.objects.create(user=user, course=course)
        modules = Module.objects.bulk_create([
            Module(course=course, title=f'Module {number}')
            for number in range(101)
        ])
        Progress.objects.create(user=user, module=modules[0], is_completed=True)

        self.assertEqual(enrollment.progress_percentage, 0.99)
