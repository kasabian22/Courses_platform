from django.test import TestCase
from django.contrib.auth.models import User

from .models import Course, Enrollment, Module, Progress, Subject


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
