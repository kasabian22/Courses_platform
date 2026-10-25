from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """Custom token generator that invalidates the token once user.is_active becomes True or email changes."""
    def _make_hash_value(self, user, timestamp):
        email_field = user.get_email_field_name()
        email = getattr(user, email_field, "") or ""
        return f"{user.pk}{timestamp}{user.is_active}{email}"


email_verification_token = EmailVerificationTokenGenerator()