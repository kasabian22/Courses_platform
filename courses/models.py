import os

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.utils.text import slugify
from .utils import generate_unique_slug


# Create your models here.
class Subject(models.Model):
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True)
    description = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title

class Course(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'AV', 'Available'
        DRAFT = 'DF', 'Draft'
    owner = models.ForeignKey(User, related_name='courses_created', on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, related_name='courses', on_delete=models.CASCADE)
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True, blank=True, null=True)
    overview = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=2, choices=Status.choices, default=Status.AVAILABLE)
    students = models.ManyToManyField(User, through='Enrollment', related_name='enrolled_courses', blank=True)

    class Meta:
        ordering = ['-date_created']

    def __str__(self):
        return self.title

    #
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Track the initial title in memory to avoid extra database queries later
        self._initial_title = self.title

    def save(self, *args, **kwargs):
        # Generate a new slug if it is empty OR if the title has changed
        if not self.slug or self.title != self._initial_title:
            # i didn't use normal slugify, because it will give IntegrityError as soon as someone use the title of a course that it's used before.
            self.slug = generate_unique_slug(self, self.title)
        super().save(*args, **kwargs)

        # Update the tracked title after a successful save
        self._initial_title = self.title


class Module(models.Model):
    course = models.ForeignKey(Course, related_name='modules', on_delete=models.CASCADE)
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.title 



class Content(models.Model):
    module = models.ForeignKey(Module, related_name='contents', on_delete=models.CASCADE)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, limit_choices_to={'model__in': ('text', 'file', 'video', 'image')})
    object_id = models.PositiveIntegerField()

    item = GenericForeignKey('content_type', 'object_id')


class Enrollment(models.Model):
    user = models.ForeignKey(User, related_name='students_enrolled', on_delete=models.CASCADE)
    course = models.ForeignKey(Course, related_name='courses_enrolled', on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        # Enforce database-level uniqueness to prevent a user from enrolling in the same course twice
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'course'], 
                name='unique_user_course_enrollment'
            )
        ]

    @property
    def progress_percentage(self):
        total_modules = self.course.modules.count()
        
        if total_modules == 0:
            return 0
            
        completed_modules = self.user.students_progress.filter(
            module__course=self.course,
            is_completed=True
        ).count()
        
        percentage = (completed_modules / float(total_modules)) * 100.0

        return round(percentage, 2)

    def __str__(self):
        return f"{self.user.username} enrolled in {self.course.title}"

class Progress(models.Model):
    user = models.ForeignKey(User, related_name='students_progress', on_delete=models.CASCADE)
    module = models.ForeignKey(Module, related_name='students_completed_modules', on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now=True)
    class Meta:
        # Enforce database-level uniqueness to prevent a user from enrolling in the same course twice
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'module'], 
                name='unique_user_content_progress'
            )
        ]
    

# This Model is an abstract Model, means that it's not created in the database, but other models can inherit from it, and we benefit from that because we don't repeat our code.
class ItemBase(models.Model):
    owner = models.ForeignKey(User, related_name='%(class)s_related', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    date_created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # delete the content when item is deleted
    content_relation = GenericRelation(Content)

    class Meta:
        abstract = True

    def __str__(self):
        return self.title



class File(ItemBase):
    file = models.FileField(upload_to="files")
    # Property to extract only the base filename without the folder path
    @property
    def filename(self):
        return os.path.basename(self.file.name)


class Image(ItemBase):
    # Use ImageField instead of FileField to validate if the file uploaded is image with pillow library.
    image = models.ImageField(upload_to="images")


class Video(ItemBase):
    # using URL instead of uplaoding the video itself, means that the instructor uploads the video on another platform (like youtube), and then use the url on our site and we render it using a built-in package in django.
    video = models.URLField()


class Text(ItemBase):
    content = models.TextField()