from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect

from courses.models import Course
from .forms import SignUpForm, InstructorProfileForm, StudentProfileForm, UserUpdateForm, CustomSignInForm, assign_instructor_permissions
from django.contrib.auth import login, logout
from .models import InstructorProfile, StudentProfile, UserProfile
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages


def sign_up(request):
    if request.user.is_authenticated:
        return redirect('courses:subject_courses_list')
    
    if request.method == 'POST':
        # the handling of the profile and it's role is in forms.py.
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # specifying the backend is necessary when using django-allauth (we use google), otherwise it will throw an error.
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('accounts:view_profile')
    else:
        form = SignUpForm()
    return render(request, 'accounts/sign_up.html', {
        'form': form
    })

def sign_in(request):
    if request.user.is_authenticated:
        return redirect('courses:subject_courses_list')

    if request.method == 'POST':
        form = CustomSignInForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('courses:subject_courses_list')
    else:
        form = CustomSignInForm()

    return render(request, 'accounts/sign_in.html', {
        'form': form
    })


@require_POST
def sign_out(request):
    logout(request)
    return redirect('accounts:sign_in')

@login_required
def edit_instructor_profile(request):
    profile, _ = InstructorProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        p_form = InstructorProfileForm(request.POST, request.FILES, instance=profile)
        u_form = UserUpdateForm(request.POST, instance=request.user)
        if p_form.is_valid() and u_form.is_valid():
            p_form.save()
            u_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:view_profile')
    else:
        p_form = InstructorProfileForm(instance=profile)
        u_form = UserUpdateForm(instance=request.user)

    return render(request, 'accounts/edit_profile.html', {
        'p_form': p_form,
        'u_form': u_form,
    })


@login_required
def edit_student_profile(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        p_form = StudentProfileForm(request.POST, request.FILES, instance=profile)
        u_form = UserUpdateForm(request.POST, instance=request.user)
        if p_form.is_valid() and u_form.is_valid():
            p_form.save()
            u_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:view_profile')
    else:
        p_form = StudentProfileForm(instance=profile)
        u_form = UserUpdateForm(instance=request.user)

    return render(request, 'accounts/edit_profile.html', {
        'p_form': p_form,
        'u_form': u_form,
    })



@login_required
def view_profile(request):
    if not request.user.is_superuser and not request.user.is_staff:
        user_profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'role': 'student'}
        )
        role = user_profile.role
        if role == "student":
            profile, _ = StudentProfile.objects.get_or_create(user=request.user)
            enrolled_courses = Course.objects.filter(students=request.user).select_related(
                'owner', 'owner__instructors_profiles'
            ).annotate(
                enrolled_students_count=Count('students', distinct=True)
            )
            return render(request, 'accounts/view_student_profile.html', {
                'profile': profile,
                'enrolled_courses': enrolled_courses
            })

        elif role == "instructor":
            profile, _ = InstructorProfile.objects.get_or_create(user=request.user)
            courses = Course.objects.filter(owner=request.user).select_related(
                'owner', 'owner__instructors_profiles'
            ).annotate(
                enrolled_students_count=Count('students', distinct=True)
            )
            return render(request, 'accounts/view_instructor_profile.html', {
                'profile': profile,
                'courses': courses
            })
    # admin or superuser
    else:
        profile, _ = InstructorProfile.objects.get_or_create(user=request.user)
        courses = Course.objects.filter(owner=request.user).select_related(
            'owner', 'owner__instructors_profiles'
        ).annotate(
            enrolled_students_count=Count('students', distinct=True)
        )
        return render(request, 'accounts/view_instructor_profile.html', {
            'profile': profile,
            'courses': courses
            })
    
@require_POST
@login_required
@transaction.atomic
def upgrade_to_instructor(request):
    student_profile = StudentProfile.objects.filter(user=request.user).first()

    if student_profile and student_profile.is_eligible_for_instructor:
        # 1. Update role in UserProfile
        UserProfile.objects.update_or_create(
            user=request.user,
            defaults={'role': 'instructor'}
        )

        # 2. Copy all shared BaseProfile data to the new InstructorProfile so nothing is lost
        InstructorProfile.objects.update_or_create(
            user=request.user,
            defaults={
                'photo': student_profile.photo,
                'bio': student_profile.bio,
                'full_name': student_profile.full_name,
                'country': student_profile.country,
                'education': student_profile.education,
                'primary_language_spoken': student_profile.primary_language_spoken,
                'linkedin': student_profile.linkedin,
                'github': student_profile.github,
                'facebook': student_profile.facebook,
            }
        )

        # 3. Grant instructor permissions for courses/modules/contents
        assign_instructor_permissions(request.user)

        # 4. Safely delete the old StudentProfile
        student_profile.delete()
        messages.success(request, "Congratulations! Your account has been upgraded to Instructor.")

    return redirect('accounts:view_profile')

def public_instructor_profile(request, instructor_id):
    instructor_profile = get_object_or_404(
        InstructorProfile.objects.select_related('user'),
        user__id=instructor_id
    )

    courses = Course.objects.filter(
        owner=instructor_profile.user,
        status=Course.Status.AVAILABLE
    ).select_related('subject').annotate(
        enrolled_students_count=Count('students', distinct=True),
        annotated_reviews_count=Count('review_details', distinct=True),
        annotated_avg_rating=Avg('review_details__rating')
    )

    return render(request, 'accounts/public_instructor_profile.html', {
        'profile': instructor_profile,
        'courses': courses
    })

# TODO
@login_required
def change_password(request):
    # Check if the user already has a password (normal signup) or not (Google/Social signup)
    FormClass = PasswordChangeForm if request.user.has_usable_password() else SetPasswordForm

    if request.method == 'POST':
        # first parameter must be the user instance.
        form = FormClass(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Keep the user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been updated successfully!')
            return redirect('accounts:view_profile')
    else:
        form = FormClass(user=request.user)

    return render(request, 'accounts/change_password.html', {'form': form})
