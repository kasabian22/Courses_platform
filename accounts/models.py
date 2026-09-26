from django.db import models
from django.contrib.auth.models import User
from django.templatetags.static import static


class InstructorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='Instructor/photos', blank=True, null=True, default='defaults/no-profile-picture-icon.png')
    contact_email = models.EmailField(blank=True, null=True)
    header = models.CharField(max_length=250, blank=True, null=True)

    def __str__(self):
        return f'Profile of {self.user.username}'


class SocialMediaAccounts(models.Model):
    user = models.OneToOneField(InstructorProfile, on_delete=models.CASCADE, related_name='socialmedia')
    linkedin = models.URLField(blank=True, null=True)
    github = models.URLField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)