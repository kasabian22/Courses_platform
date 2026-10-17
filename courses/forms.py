from django import forms
from .models import Course, Text, Video, Image, File, Module, Review


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['subject', 'title', 'header', 'overview', 'status', 'level', 'language', 'time_to_complete', 'image']


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title', 'description']


class TextForm(forms.ModelForm):
    class Meta:
        model = Text
        fields = ['title', 'content']

class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['title', 'video']

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