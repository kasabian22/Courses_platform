from django.shortcuts import get_object_or_404, render, redirect

from courses.models import Course
from .forms import SignUpForm, InstructorProfileForm, StudentProfileForm, UserUpdateForm
from django.contrib.auth import login, logout, authenticate
from .models import InstructorProfile, StudentProfile
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash


def sign_up(request):
    if request.method == 'POST':
        # the handling of the profile and it's role is in forms.py.
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('accounts:view_profile')
    else:
        form = SignUpForm()
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


@require_POST
def sign_out(request):
    logout(request)
    return redirect('accounts:sign_up')

@login_required(login_url='accounts:sign_up')
def edit_instructor_profile(request):
    profile = get_object_or_404(InstructorProfile, user=request.user)
    p_form = InstructorProfileForm(instance=profile)
    u_form = UserUpdateForm(instance=request.user)
    if request.method == 'POST':
        p_form = InstructorProfileForm(request.POST, request.FILES, instance=profile)
        u_form = UserUpdateForm(request.POST, instance=request.user)
        if p_form.is_valid() and u_form.is_valid():
            p_form.save()
            u_form.save()
            return redirect('accounts:view_profile')
    

    return render(request, 'accounts/edit_profile.html', {
        'p_form': p_form,
        'u_form': u_form,
    })


@login_required(login_url='accounts:sign_up')
def edit_student_profile(request):
    profile = get_object_or_404(StudentProfile, user=request.user)
    p_form = StudentProfileForm(instance=profile)
    u_form = UserUpdateForm(instance=request.user)
    if request.method == 'POST':
        p_form = StudentProfileForm(request.POST, request.FILES, instance=profile)
        u_form = UserUpdateForm(request.POST, instance=request.user)
        if p_form.is_valid() and u_form.is_valid():
            p_form.save()
            u_form.save()
            return redirect('accounts:view_profile')
    

    return render(request, 'accounts/edit_profile.html', {
        'p_form': p_form,
        'u_form': u_form,
    })



@login_required(login_url='accounts:sign_up')
def view_profile(request):
    if hasattr(request.user, 'userprofile'):
        role = request.user.userprofile.role
        if role == "student":
            profile = get_object_or_404(StudentProfile, user=request.user)
            enrolled_courses = Course.objects.filter(students=request.user)
            return render(request, 'accounts/view_student_profile.html', {
                'profile': profile,
                'enrolled_courses': enrolled_courses
            })
    
    profile = get_object_or_404(InstructorProfile, user=request.user)
    courses = Course.objects.filter(owner=request.user)
    return render(request, 'accounts/view_instructor_profile.html', {
        'profile': profile,
        'courses': courses
    })

    # return redirect('subject_courses_list')




# TODO
# @login_required
# def change_password(request):
#     if request.method == 'POST':
#         # لاحظ أن PasswordChangeForm يأخذ request.user كأول معامل وليس instance=
#         form = PasswordChangeForm(user=request.user, data=request.POST)
#         if form.is_valid():
#             user = form.save()  # هنا يقوم بتشفير الباسورد الجديد وحفظه بأمان
            
#             # هذا السطر يحافظ على بقاء المستخدم مسجلاً للدخول بعد تغيير الباسورد
#             update_session_auth_hash(request, user)
#             return redirect('accounts:view_profile')
#     else:
#         form = PasswordChangeForm(user=request.user)

#     return render(request, 'accounts/change_password.html', {'form': form})
