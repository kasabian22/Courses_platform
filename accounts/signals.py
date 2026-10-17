from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from .models import UserProfile, StudentProfile


@receiver(user_signed_up)
def create_social_profile(request, user, sociallogin=None, **kwargs):
    if sociallogin:
        UserProfile.objects.get_or_create(
            user=user,
            defaults={'role': 'student'}
        )

        # Extract full name from Google/Social account data if available
        full_name = user.get_full_name() or sociallogin.account.extra_data.get('name', '')
        StudentProfile.objects.get_or_create(
            user=user,
            defaults={'full_name': full_name[:100]}
        )