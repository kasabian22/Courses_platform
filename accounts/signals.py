from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from .models import UserProfile, StudentProfile


# This signal is responsible for connecting Google / Social Authentication to our custom profile models.
# Without this signal, any user signing up with Google would be created without an associated UserProfile or StudentProfile.
@receiver(user_signed_up)
def create_social_profile(request, user, sociallogin=None, **kwargs):
    if sociallogin:
        # Ensure UserProfile exists with default role 'student'
        UserProfile.objects.get_or_create(
            user=user,
            defaults={'role': 'student'}
        )
        # Extract full name from Google/Social account data if available
        full_name = user.get_full_name() or sociallogin.account.extra_data.get('name', '')
        # Create their StudentProfile with their name prefilled
        StudentProfile.objects.get_or_create(
            user=user,
            defaults={'full_name': full_name[:100]}
        )