from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect

from courses.models import Course
from .forms import SignUpForm, InstructorProfileForm, StudentProfileForm, UserUpdateForm, CustomSignInForm, assign_instructor_permissions
from django.contrib.auth import login, logout
from .models import InstructorProfile, InstructorRequest, StudentProfile, UserProfile
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Min
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages


# region ======================================================    Authorization    ==============================================================

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


# endregion ===================================================================================================================

# region ======================================================       Profile       ==============================================================

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
                'owner__instructors_profiles'
            ).annotate(
                enrolled_students_count=Count('students', distinct=True),
                annotated_avg_rating=Avg('review_details__rating'),
                annotated_reviews_count=Count('review_details', distinct=True),
                enrollment_date=Min('students_enrolled__enrolled_at')
            ).order_by(
                'enrollment_date'
            )

            user_request = request.user.instructor_requests.first()
            show_request_banner = False

            if user_request:
                if user_request.status in ['approved', 'pending']:
                    show_request_banner = True
                    
                elif user_request.status == 'rejected' and not user_request.is_seen:
                    show_request_banner = True
                    
                    user_request.is_seen = True
                    user_request.save()

            return render(request, 'accounts/view_student_profile.html', {
                'profile': profile,
                'enrolled_courses': enrolled_courses,
                'user_request': user_request,
                'show_request_banner': show_request_banner,
            })

        elif role == "instructor":
            profile, _ = InstructorProfile.objects.get_or_create(user=request.user)
            courses = Course.objects.filter(owner=request.user).select_related(
                'owner__instructors_profiles'
            ).annotate(
                enrolled_students_count=Count('students', distinct=True),
                annotated_avg_rating=Avg('review_details__rating'),
                annotated_reviews_count=Count('review_details', distinct=True)
            ).order_by(
                'id'
            )

            return render(request, 'accounts/view_instructor_profile.html', {
                'profile': profile,
                'courses': courses
            })
    # admin or superuser
    else:
        profile, _ = InstructorProfile.objects.get_or_create(user=request.user)
        courses = Course.objects.filter(owner=request.user).select_related(
            'owner__instructors_profiles'
        ).annotate(
            enrolled_students_count=Count('students', distinct=True)
        )
        return render(request, 'accounts/view_instructor_profile.html', {
            'profile': profile,
            'courses': courses
            })


def public_instructor_profile(request, instructor_id):
    instructor_profile = get_object_or_404(
        InstructorProfile.objects.select_related('user'),
        user__id=instructor_id
    )

    courses = Course.objects.filter(
        owner=instructor_profile.user,
        status=Course.Status.AVAILABLE
    ).select_related('owner__instructors_profiles').annotate(
        enrolled_students_count=Count('students', distinct=True),
        annotated_reviews_count=Count('review_details', distinct=True),
        annotated_avg_rating=Avg('review_details__rating')
    )

    return render(request, 'accounts/public_instructor_profile.html', {
        'profile': instructor_profile,
        'courses': courses
    })



@login_required
@transaction.atomic
def edit_profile(request):
    user_profile, _ = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'role': 'student'}
    )
    is_instructor = request.user.is_staff or request.user.is_superuser or user_profile.role == 'instructor'
    # Dynamically select the profile model and form based on user role
    if is_instructor:
        profile, _ = InstructorProfile.objects.get_or_create(user=request.user)
        ProfileFormClass = InstructorProfileForm
    else:
        profile, _ = StudentProfile.objects.get_or_create(user=request.user)
        ProfileFormClass = StudentProfileForm
    if request.method == 'POST':
        p_form = ProfileFormClass(request.POST, request.FILES, instance=profile)
        u_form = UserUpdateForm(request.POST, instance=request.user)
        if p_form.is_valid() and u_form.is_valid():
            p_form.save()
            u_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:view_profile')
    else:
        p_form = ProfileFormClass(instance=profile)
        u_form = UserUpdateForm(instance=request.user)
    return render(request, 'accounts/edit_profile.html', {
        'p_form': p_form,
        'u_form': u_form,
    })



# endregion ===============================================================================================================

# region ======================================================   Upgrade profile  ==============================================================
@login_required
@require_POST
def send_instructor_request(request):
    if hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'student':
        request_exists = InstructorRequest.objects.filter(user=request.user).exists()
        
        if not request_exists:
            InstructorRequest.objects.create(user=request.user)
            messages.success(request, "Your request to become an instructor has been sent successfully!")
        else:
            messages.info(request, "You have already submitted a request.")
            
    return redirect('accounts:view_profile')
    # Returning to the same page from which the student clicked the button
    # return redirect(request.META.get('HTTP_REFERER', '/'))


@require_POST
@login_required
@transaction.atomic
def upgrade_to_instructor(request):
    student_profile = StudentProfile.objects.filter(user=request.user).first()
    
    # Check if the user has an approved instructor request instead of the old boolean field
    approved_request = InstructorRequest.objects.filter(user=request.user, status='approved').first()

    if student_profile and approved_request:
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
        
        # 5. Delete the request record or mark it as completed so it doesn't stay in the DB forever
        approved_request.delete() 

        messages.success(request, "Congratulations! Your account has been upgraded to Instructor.")
        
    return redirect('accounts:view_profile')


# endregion

