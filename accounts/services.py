# Services.py should handle business logic and database transitions. Keeping database transactions out of the view means you can reuse the upgrade logic later (e.g., from the Django Admin actions, an automated test, or an API) without duplicating code.


from django.contrib.auth.models import Permission
from django.db import transaction
from .models import UserProfile, InstructorProfile, StudentProfile


def assign_instructor_permissions(user):
    """Grant course, module, and content management permissions to an instructor."""
    codenames = [
        'add_course', 'change_course', 'delete_course',
        'add_module', 'change_module', 'delete_module',
        'add_content', 'change_content', 'delete_content',
    ]
    permissions = Permission.objects.filter(
        content_type__app_label='courses',
        codename__in=codenames
    )
    user.user_permissions.add(*permissions)


@transaction.atomic
def process_instructor_upgrade(user, student_profile, approved_request):
    """Encapsulates all database operations to upgrade a student to an instructor."""
    # 1. Update role
    UserProfile.objects.update_or_create(user=user, defaults={'role': 'instructor'})

    # 2. Copy BaseProfile data
    InstructorProfile.objects.update_or_create(
        user=user,
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

    # 3. Assign permissions
    assign_instructor_permissions(user)

    # 4. Safely detach and delete old student profile
    photo_file = student_profile.photo
    StudentProfile.objects.filter(pk=student_profile.pk).update(photo=None)
    student_profile.delete()

    if photo_file:
        InstructorProfile.objects.filter(user=user).update(photo=photo_file)

    # 5. Remove or finish request
    approved_request.delete()