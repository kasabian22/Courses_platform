from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import InstructorProfile

class SignUpForm(UserCreationForm):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('insrtuctor', 'Insrtuctor')
    )

    # the variable name 'username' must be the same as the field item 'username' and so on...
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Enter Your Username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder':'Enter Your Email'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Enter Your Password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Enter Confirmation Password'}))

    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)


    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']



class InstructorProfileForm(forms.ModelForm):
    class Meta:
        model = InstructorProfile
        fields = ['bio', 'photo', 'contact_email', 'header']