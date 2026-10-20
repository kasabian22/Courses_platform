import os
import re
from urllib.parse import parse_qs, urlsplit
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.utils.text import slugify
from .utils import extract_smart_base_slug, generate_unique_slug
from django_quill.fields import QuillField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
from django.conf.global_settings import LANGUAGES
from unidecode import unidecode


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
    title = models.CharField(max_length=250, help_text="Write the title of the course here (Must contain English characters or numbers)")
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    overview = QuillField(help_text="Write the description of the course here")
    header = models.CharField(max_length=250, blank=True, null=True, help_text="Write the header that appers below the course title both on the course card, and in the course page (optional)")
    date_created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=2, choices=Status.choices, default=Status.AVAILABLE)
    students = models.ManyToManyField(User, through='Enrollment', related_name='enrolled_courses', blank=True)
    wishlist = models.ManyToManyField(User, related_name='wishlist', blank=True)
    level = models.CharField(max_length=50, choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')], default='beginner')
    time_to_complete = models.DurationField(help_text="Enter the course duration in HH:MM:SS format (e.g., 02:30:00 for 2 and a half hours)", null=True, blank=True)
    reviews = models.ManyToManyField(User, through='Review', related_name='course_reviews', blank=True)
    language = models.CharField(max_length=50, choices=LANGUAGES, default='en', help_text="Select the language of the course")
    image = models.ImageField(upload_to='course_images/', null=True, blank=True, help_text="Upload an image for the course (Recommended aspect ratio: 16:9)")
    
    @property
    def students_count(self):
        # Use annotated value if available to avoid N+1 queries
        if hasattr(self, 'enrolled_students_count'):
            return self.enrolled_students_count
        return self.students.count()
    
    @property
    def reviews_count(self):
        if hasattr(self, 'annotated_reviews_count'):
            return self.annotated_reviews_count
        return self.review_details.count()
   
    @property
    def average_rating(self):
        if hasattr(self, 'annotated_avg_rating'):
            return round(self.annotated_avg_rating, 1) if self.annotated_avg_rating is not None else 0.0
        avg = self.review_details.aggregate(Avg('rating'))['rating__avg']
        
        if avg is not None:
            return round(avg, 1)  
        # No reviews yet, return 0.0 as the average rating
        return 0.0

    @property
    def bestseller_badge(self):
        # Returns True automatically if students count is 2 or more, otherwise False
        return self.students_count >= 2
    


    class Meta:
        ordering = ['-date_created']
        indexes = [
            models.Index(fields=['status', '-date_created']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(slug=""),
                name="course_slug_not_empty"
            )
        ]

    def __str__(self):
        return self.title

    #
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Track the initial title in memory to avoid extra database queries later
        # The title is stored when the object is created or loaded.
        self._initial_title = self.title

    def clean(self):
        super().clean()
        # Ensure title has at least three valid Arabic/English letters or numbers
        if self.title and not re.search(r"[a-zA-Z0-9\u0600-\u06FF]{3,}", self.title):
            raise ValidationError({
                'title': "Course title must contain valid Arabic or English letters or numbers."
            })

        # Ensure that either the custom slug or the title produces a valid slug
        valid_slug = slugify(unidecode(self.slug)) if self.slug else extract_smart_base_slug(self.title)
        if not valid_slug:
            raise ValidationError({
                'slug': "Could not generate a valid URL slug. Please enter a valid custom slug using English letters and numbers."
            })

    def save(self, *args, **kwargs):
        # If slug is empty, or if title changed without a custom slug override, generate a unique one
        if not self.slug or self.title != self._initial_title:
            self.slug = generate_unique_slug(self, title=self.title)
        else:
            # Sanitize and guarantee uniqueness even if a custom slug was provided
            self.slug = generate_unique_slug(self, title=self.title, custom_slug=self.slug)

        # Final database guard: never allow an empty slug into PostgreSQL
        if not self.slug or not self.slug.strip():
            raise ValidationError("Integrity guard: Course slug cannot be empty.")

        super().save(*args, **kwargs)
        # Update the initial title after saving to reflect the current state
        self._initial_title = self.title


class Module(models.Model):
    course = models.ForeignKey(Course, related_name='modules', on_delete=models.CASCADE)
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.title
    class Meta: 
        ordering = ['id']



class Content(models.Model):
    module = models.ForeignKey(Module, related_name='contents', on_delete=models.CASCADE)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, limit_choices_to={'model__in': ('text', 'file', 'video', 'image')})
    object_id = models.PositiveIntegerField()

    item = GenericForeignKey('content_type', 'object_id')
    class Meta: 
        ordering = ['id']


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
    
class Review(models.Model):
    user = models.ForeignKey(User, related_name='reviews', on_delete=models.CASCADE)
    course = models.ForeignKey(Course, related_name='review_details', on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Enforce database-level uniqueness to prevent a user from reviewing the same course twice
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'course'], 
                name='unique_user_course_review'
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
    video_url = models.URLField(null=True, blank=True, help_text="Enter a youtube video URL (optional). If provided, this will be used instead of uploading a video file.")
    video_upload = models.FileField(upload_to="videos", null=True, blank=True, help_text="Upload a video file (optional). If provided, this will be used instead of the URL.")

    @property
    def youtube_embed_url(self):
        if not self.video_url:
            return ''

        parsed_url = urlsplit(self.video_url)
        host = (parsed_url.hostname or '').lower()
        youtube_hosts = {'youtube.com', 'www.youtube.com', 'm.youtube.com'}

        if host == 'youtu.be':
            video_id = parsed_url.path.strip('/').split('/')[0]
        elif host in youtube_hosts and parsed_url.path == '/watch':
            video_id = parse_qs(parsed_url.query).get('v', [''])[0]
        elif host in youtube_hosts:
            path_segments = parsed_url.path.strip('/').split('/')
            if path_segments[0] == 'embed':
                return self.video_url
            if len(path_segments) > 1 and path_segments[0] in {'shorts', 'live'}:
                video_id = path_segments[1]
            else:
                return self.video_url
        else:
            return self.video_url

        if video_id:
            return f'https://www.youtube.com/embed/{video_id}'
        return self.video_url

class Text(ItemBase):
    content = models.TextField()