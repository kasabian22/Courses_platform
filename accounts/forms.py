from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import InstructorProfile, StudentProfile, UserProfile
from django.contrib.auth.forms import AuthenticationForm


class SignUpForm(UserCreationForm):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('instructor', 'Instructor')
    )

    # the variable name 'email' must be the same as the field item 'email' and so on...
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)


    class Meta:
        model = User
        # we don't add role field because we add only fields that is related to User model, and role added automatially because it's a Declarative Field, but doesn't saved in user model, but saved in UserProfile model that we added before
        fields = ['username', 'email']

    # validation for repitive emails.
    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered. Please use a different one.")
        
        return email
    
    # We add here the placeholders of the fields, and hiding help_text that appers always under fields in default settings.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['username'].widget.attrs['placeholder'] = 'Enter Your Username'
        self.fields['email'].widget.attrs['placeholder'] = 'Enter Your Email'
        self.fields['password1'].widget.attrs['placeholder'] = 'Enter Your Password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Enter Confirmation Password'

        self.fields['username'].help_text = ''
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''
    
    def save(self, commit=True):
        user = super().save(commit=commit)

        if commit:
            selected_role = self.cleaned_data.get('role')

            UserProfile.objects.update_or_create(
                user=user,
                defaults={'role': selected_role}
            )

            # this is one of three ways to add profile when the user makes an account, the second way is made with signals in models.py file, the third is to take the same line and use it in views.py.
            if selected_role == 'student':
                StudentProfile.objects.create(user=user)
            elif selected_role == 'instructor':
                InstructorProfile.objects.create(user=user)

        return user

# I added this (over AuthenticationForm) to be able to use placeholders in the sign-in form.
class CustomSignInForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'Enter Your Username'
        self.fields['password'].widget.attrs['placeholder'] = 'Enter Your Password'


class InstructorProfileForm(forms.ModelForm):
    class Meta:
        model = InstructorProfile
        fields = ['bio', 'photo', 'contact_email', 'header']


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile  
        fields = ["photo", "bio"]


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']