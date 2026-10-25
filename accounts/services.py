from django.conf import settings
from django.contrib.auth.models import Permission
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .tokens import email_verification_token


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


def send_verification_email(request, user):
    """Generates an activation token and sends a verification email to the user."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)
    verify_url = request.build_absolute_uri(
        reverse('accounts:verify_email', kwargs={'uidb64': uid, 'token': token})
    )

    # In local development, print the clean, unwrapped URL directly to stdout
    # so developers can click it with 1 click without MIME quoted-printable line breaks ('=\n')
    if getattr(settings, 'DEBUG', False):
        print("\n" + "=" * 78)
        print("[EMAIL VERIFICATION LINK] (Click to activate):")
        print(verify_url)
        print("=" * 78 + "\n")

    subject = "Verify your email - E-Learning Platform"
    context = {
        'user': user,
        'verify_url': verify_url,
    }
    text_message = render_to_string('accounts/emails/verify_email.txt', context)
    html_message = render_to_string('accounts/emails/verify_email.html', context)
    send_mail(
        subject=subject,
        message=text_message,
        from_email=None,
        recipient_list=[user.email],
        html_message=html_message,
    )


