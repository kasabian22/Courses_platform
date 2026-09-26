from django.shortcuts import get_object_or_404, render, redirect

from courses.models import Course
from .forms import SignUpForm, InstructorProfileForm
from django.contrib.auth import login, logout, authenticate
from .models import InstructorProfile
from django.contrib.auth.decorators import login_required

def sign_up(request):
    form = SignUpForm()
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # this is one of two ways to add profile when the instructor makes an account, the second way is made with signals in models.py file.
            InstructorProfile.objects.create(user=user)

            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('accounts:view_profile')
    return render(request, 'accounts/sign_up.html', {
        'form': form
    })

def sign_in(request):
    ERROR = None
    if request.user.is_authenticated:
        return redirect('courses:subject_courses_list')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('courses:subject_courses_list')
        else:
            ERROR = 'Invalid credentials! Password or username is invalid!'

    return render(request, 'accounts/sign_in.html', {
        'error': ERROR
    })



def sign_out(request):
    logout(request)
    return redirect('accounts:sign_up')

@login_required(login_url='accounts:sign_up')
def edit_profile(request):
    profile = get_object_or_404(InstructorProfile, user=request.user)
    form = InstructorProfileForm(instance=profile)
    if request.method == 'POST':
        form = InstructorProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('accounts:view_profile')
    

    return render(request, 'accounts/edit_profile.html', {
        'form': form,
    })


@login_required(login_url='accounts:sign_up')
def view_profile(request):
    profile = get_object_or_404(InstructorProfile, user=request.user)
    courses = Course.objects.filter(owner=request.user)
    return render(request, 'accounts/view_profile.html',{
        'profile': profile,
        'courses': courses
    })



