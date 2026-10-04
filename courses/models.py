from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
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
    students = models.ManyToManyField(User, related_name='enrolled_courses', blank=True)

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

    def __str__(self):
        return self.title 


class Content(models.Model):
    module = models.ForeignKey(Module, related_name='contents', on_delete=models.CASCADE)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, limit_choices_to={'model__in': ('text', 'file', 'video', 'image')})
    object_id = models.PositiveIntegerField()

    item = GenericForeignKey('content_type', 'object_id')


# This Model is an abstract Model, means that it's not created in the database, but other models can inherit from it, and we benefit from that because we don't repeat our code.
class ItemBase(models.Model):
    owner = models.ForeignKey(User, related_name='%(class)s_related', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    date_created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.title



class File(ItemBase):
    file = models.FileField(upload_to="files")


class Image(ItemBase):
    # Use ImageField instead of FileField to validate if the file uploaded is image with pillow library.
    image = models.ImageField(upload_to="images")


class Video(ItemBase):
    # using URL instead of uplaoding the video itself, means that the instructor uploads the video on another platform (like youtube), and then use the url on our site and we render it using a built-in package in django.
    video = models.URLField()


class Text(ItemBase):
    content = models.TextField()