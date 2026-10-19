import os
import re
from django import forms
from .models import Course, Text, Video, Image, File, Module, Review
from django.core.exceptions import ValidationError


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['subject', 'title', 'header', 'overview', 'status', 'level', 'language', 'time_to_complete', 'image']

    def clean_title(self):
        title = self.cleaned_data.get('title')
        
        # 1. Check that all characters are English letters, numbers, or basic punctuation
        if not re.match(r"^[a-zA-Z0-9\s\-_.,!?()'\"]+$", title):
            raise ValidationError("The course title must be in English only. Please do not use Arabic or other alphabets.")
            
        # 2. Ensure the title contains at least one English letter or number (not just punctuation/spaces)
        if not re.search(r"[a-zA-Z0-9]", title):
            raise ValidationError("The course title must contain at least one English letter or number.")
            
        return title


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
        if video_file:
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
    class Meta:
        model = File
        fields = ['title', 'file']

class ImageForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ['title', 'image']


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']