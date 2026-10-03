from django.db import models
from django.contrib.auth.models import User
from django.templatetags.static import static

# Additional fields to the default User model.
# There is another way using AbstractUser but this way benefits when you already started the project and have data in the database.
# write request.user.userprofile.field_name anywhere in the project to use it.
class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('instructor', 'Instructor'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='students_profiles')
    photo = models.ImageField(upload_to='Student/photos', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    full_name = models.CharField(max_length=100, blank=True)
    # TODO
    # country = models.CharField(max_length=100, blank=True, choices="")
    # education = models.CharField(max_length=100, blank=True, choices="")
    # primary_language_spoken = models.CharField(max_length=100, blank=True, choices="")
    def __str__(self):
            return f"Profile of {self.user.username}"


class InstructorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructors_profiles')
    bio = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='Instructor/photos', blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    header = models.CharField(max_length=250, blank=True, null=True)

    def __str__(self):
        return f'Profile of {self.user.username}'


class SocialMediaAccounts(models.Model):
    instructor_profile = models.OneToOneField(InstructorProfile, on_delete=models.CASCADE, related_name='socialmedia')
    linkedin = models.URLField(blank=True, null=True)
    github = models.URLField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)