from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect

from courses.models import Course
from .forms import SignUpForm, InstructorProfileForm, StudentProfileForm, UserUpdateForm, CustomSignInForm
from django.contrib.auth import login, logout
from .models import InstructorProfile, InstructorRequest, StudentProfile, UserProfile
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Min
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from .services import process_instructor_upgrade
from django.contrib.auth.models import User

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
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
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
                'owner__instructor_profile'
            ).annotate(
                enrolled_students_count=Count('students', distinct=True),
                annotated_avg_rating=Avg('review_details__rating'),
                annotated_reviews_count=Count('review_details', distinct=True),
                enrollment_date=Min('students__students_enrolled__enrolled_at')
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
                    

            return render(request, 'accounts/view_student_profile.html', {
                'profile': profile,
                'enrolled_courses': enrolled_courses,
                'user_request': user_request,
                'show_request_banner': show_request_banner,
            })

        elif role == "instructor":
            profile, _ = InstructorProfile.objects.get_or_create(user=request.user)
            courses = Course.objects.filter(owner=request.user).select_related(
                'owner__instructor_profile'
            ).annotate(
                enrolled_students_count=Count('students', distinct=True),
                annotated_avg_rating=Avg('review_details__rating'),
                annotated_reviews_count=Count('review_details', distinct=True)
            ).order_by(
                'id'
            )

            enrolled_courses = Course.objects.filter(students=request.user).select_related(
                'owner__instructor_profile'
            ).annotate(
                enrolled_students_count=Count('students', distinct=True),
                annotated_avg_rating=Avg('review_details__rating'),
                annotated_reviews_count=Count('review_details', distinct=True)
            ).order_by(
                '-id'
            )

            return render(request, 'accounts/view_instructor_profile.html', {
                'profile': profile,
                'courses': courses,
                'enrolled_courses': enrolled_courses,
            })
    # admin or superuser
    else:
        profile, _ = InstructorProfile.objects.get_or_create(user=request.user)
        courses = Course.objects.filter(owner=request.user).select_related(
            'owner__instructor_profile'
        ).annotate(
            enrolled_students_count=Count('students', distinct=True)
        )

        enrolled_courses = Course.objects.filter(students=request.user).select_related(
                'owner__instructor_profile'
            ).annotate(
                enrolled_students_count=Count('students', distinct=True),
                annotated_avg_rating=Avg('review_details__rating'),
                annotated_reviews_count=Count('review_details', distinct=True)
            ).order_by(
                '-id'
            )
        return render(request, 'accounts/view_instructor_profile.html', {
            'profile': profile,
            'courses': courses,
            'enrolled_courses': enrolled_courses,
            })


def public_instructor_profile(request, instructor_id):
    user = get_object_or_404(User, id=instructor_id)
    # If the user is staff/instructor but lacks a profile row, create it safely
    instructor_profile, _ = InstructorProfile.objects.get_or_create(
        user=user,
        defaults={'full_name': user.get_full_name() or user.username}
    )

    courses = Course.objects.filter(
        owner=instructor_profile.user,
        status=Course.Status.AVAILABLE
    ).select_related('owner__instructor_profile').annotate(
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
        request_exists = InstructorRequest.objects.filter(user=request.user, status__in=['pending', 'approved']).exists()
        
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
def upgrade_to_instructor(request):
    student_profile = StudentProfile.objects.filter(user=request.user).first()
    approved_request = InstructorRequest.objects.filter(user=request.user, status='approved').first()
    if student_profile and approved_request:
        process_instructor_upgrade(request.user, student_profile, approved_request)
        messages.success(request, "Congratulations! Your account has been upgraded to Instructor.")
    return redirect('accounts:view_profile')

@require_POST
@login_required
def dismiss_instructor_request(request):
    req = request.user.instructor_requests.filter(status='rejected', is_seen=False).first()
    if req:
        req.is_seen = True
        req.save()
    return redirect('accounts:view_profile')

# endregion

