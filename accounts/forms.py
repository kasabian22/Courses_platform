from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import InstructorProfile, StudentProfile, UserProfile

class SignUpForm(UserCreationForm):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('instructor', 'Instructor')
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