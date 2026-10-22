import os
import re
from django import forms
from django.utils.text import slugify
from unidecode import unidecode

from .utils import generate_unique_slug
from .models import Course, Text, Video, Image, File, Module, Review
from django.core.exceptions import ValidationError


class CourseForm(forms.ModelForm):
    slug = forms.CharField(
        required=False,
        max_length=250,
        label="Custom URL Slug",
        help_text="Auto-generated from the title. You can customize it using lowercase English letters, numbers, and hyphens (-)."
    )
    class Meta:
        model = Course
        fields = ['subject', 'title', 'slug', 'header', 'overview', 'status', 'level', 'language', 'time_to_complete', 'image']

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        # Require at least three Arabic letters, English letters, or digits
        if not re.search(r"[a-zA-Z0-9\u0600-\u06FF]{3,}", title):
            raise ValidationError("The course title must contain at least three Arabic or English letters or numbers.")
        return title

    def clean_slug(self):
        raw_slug = self.cleaned_data.get('slug', '').strip()
        title = self.cleaned_data.get('title', '')

        # If the user typed a custom slug, validate that it can form a clean slug
        if raw_slug:
            cleaned = slugify(unidecode(raw_slug))
            if not cleaned:
                raise ValidationError("Invalid slug format. Please use English letters, numbers, and hyphens only.")
            # Guarantee uniqueness in the DB (excluding current course if editing)
            return generate_unique_slug(self.instance, title=title, custom_slug=cleaned)

        # If left empty, auto-generate from the validated title
        if title:
            return generate_unique_slug(self.instance, title=title)

        return raw_slug


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title', 'description']


class TextForm(forms.ModelForm):
    class Meta:
        model = Text
        fields = ['title', 'content']

class VideoForm(forms.ModelForm):
    # Limit maximum upload size to 100 MB (100 * 1024 * 1024 bytes)
    MAX_VIDEO_SIZE_MB = 100
    ALLOWED_EXTENSIONS = ['.mp4', '.webm']

    class Meta:
        model = Video
        fields = ['title', 'video_url', 'video_upload']
        widgets = {
            'video_upload': forms.ClearableFileInput(attrs={'accept': 'video/mp4,video/webm'}),
        }

    def clean_video_upload(self):
        video_file = self.cleaned_data.get('video_upload')
        # Only validate size and extension if a new file was actually uploaded in this request
        if video_file and 'video_upload' in self.changed_data:
            # 1. Validate file extension
            ext = os.path.splitext(video_file.name)[1].lower()
            if ext not in self.ALLOWED_EXTENSIONS:
                raise forms.ValidationError(
                    f"Unsupported file format '{ext}'. Please upload an MP4 or WebM video."
                )

            # 2. Validate file size
            max_bytes = self.MAX_VIDEO_SIZE_MB * 1024 * 1024
            if video_file.size > max_bytes:
                raise forms.ValidationError(
                    f"Video file is too large ({video_file.size / (1024 * 1024):.1f} MB). "
                    f"Maximum allowed size is {self.MAX_VIDEO_SIZE_MB} MB."
                )
        return video_file

    def clean(self):
        cleaned_data = super().clean()
        video_url = cleaned_data.get('video_url')
        video_upload = cleaned_data.get('video_upload')

        # If clean_video_upload raised an error, skip the cross-field check so the file error shows clearly
        if self.errors.get('video_upload'):
            return cleaned_data

        # Ensure the instructor provides exactly ONE video source
        if not video_url and not video_upload:
            raise forms.ValidationError(
                "Please provide either a YouTube Video URL or upload a video file."
            )

        if video_url and video_upload:
            raise forms.ValidationError(
                "Please provide only one video source (either a URL or an uploaded file, not both)."
            )

        return cleaned_data

class FileForm(forms.ModelForm):
    MAX_VIDEO_SIZE_MB = 25
    ALLOWED_EXTENSIONS = ['.pdf', '.zip', '.docx', '.pptx']
    class Meta:
        model = File
        fields = ['title', 'file']
        widgets = {
            'file': forms.ClearableFileInput(attrs={'accept': 'file/pdf,file/zip,file/docx,file/pptx'}),
        }
    
    def clean_file_upload(self):
        file = self.cleaned_data.get('file')
        if file and 'file' in self.changed_data:
            # 1. Validate file extension
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in self.ALLOWED_EXTENSIONS:
                raise forms.ValidationError(
                    f"Unsupported file format '{ext}'. Please upload an PDF or ZIP or DOCX or PPTX file."
                )
        
            # 2. Validate file size
            max_bytes = self.MAX_VIDEO_SIZE_MB * 1024 * 1024
            if file.size > max_bytes:
                raise forms.ValidationError(
                    f"The file is too large ({file.size / (1024 * 1024):.1f} MB). "
                    f"Maximum allowed size is {self.MAX_VIDEO_SIZE_MB} MB."
            )
        return file

class ImageForm(forms.ModelForm):
    MAX_VIDEO_SIZE_MB = 5
    ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]
    class Meta:
        model = Image
        fields = ['title', 'image']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'accept': 'image/jpg,image/jpeg,image/png,image/gif,image/webp,image/svg'}),
        }
        
    def clean_image_upload(self):
        image = self.cleaned_data.get('image')
        if image and 'image' in self.changed_data:
            # 1. Validate file extension
            ext = os.path.splitext(image.name)[1].lower()
            if ext not in self.ALLOWED_EXTENSIONS:
                raise forms.ValidationError(
                    f"Unsupported file format '{ext}'. Please upload an JPG or JPEG or PNG or GIF or WEBP or SVG image."
                )
        
            # 2. Validate file size
            max_bytes = self.MAX_VIDEO_SIZE_MB * 1024 * 1024
            if image.size > max_bytes:
                raise forms.ValidationError(
                    f"The image is too large ({image.size / (1024 * 1024):.1f} MB). "
                    f"Maximum allowed size is {self.MAX_VIDEO_SIZE_MB} MB."
            )
        return image


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']