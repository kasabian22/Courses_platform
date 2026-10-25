from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django_countries.fields import CountryField
from courses.models import Review
from django.utils.functional import cached_property

class EducationLevel(models.TextChoices):
    HIGH_SCHOOL = 'high_school', 'High School / Secondary'
    ASSOCIATE = 'associate', 'Associate Degree / Diploma'
    BACHELOR = 'bachelor', "Bachelor's Degree"
    MASTER = 'master', "Master's Degree"
    DOCTORATE = 'doctorate', 'Doctorate (Ph.D.)'
    OTHER = 'other', 'Other'

# Additional fields to the default User model.
# There is another way using AbstractUser, but this way benefits when you already started the project and have data in the database.
# write request.user.userprofile.field_name anywhere in the project to use it.
class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('instructor', 'Instructor'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class BaseProfile(models.Model):
    photo = models.ImageField(upload_to='photos', blank=True)
    bio = models.TextField(blank=True, default='')
    full_name = models.CharField(max_length=100, blank=True, default='')
    
    country = CountryField(
        blank=True,
        blank_label='Select Country'
    )
    education = models.CharField(
        max_length=50,
        blank=True, default='',
        choices=EducationLevel.choices
    )
    primary_language_spoken = models.CharField(
        max_length=20,
        blank=True, default='',
        choices=settings.LANGUAGES
    )

    linkedin = models.URLField(blank=True, default='')
    github = models.URLField(blank=True, default='')
    facebook = models.URLField(blank=True, default='')

    class Meta:
        abstract = True


class StudentProfile(BaseProfile):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    def __str__(self):
            return f"{self.user.username}'s Student Profile"


class InstructorProfile(BaseProfile):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructor_profile')
    contact_email = models.EmailField(blank=True, null=True)
    header = models.CharField(max_length=250, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Instructor Profile"

    @cached_property
    def total_students(self):
        return User.objects.filter(enrolled_courses__owner=self.user).distinct().count()

    @cached_property
    def total_reviews(self):
        return Review.objects.filter(course__owner=self.user).count()


class InstructorRequest(models.Model):
    user = models.ForeignKey(User, related_name='instructor_requests', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    is_seen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
        models.UniqueConstraint(
            fields=['user'],
            condition=models.Q(status='pending'),
            name='unique_pending_instructor_request'
        )
    ]

    def __str__(self):
        return f"Request by {self.user.username} - Status: {self.status}"