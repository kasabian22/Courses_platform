from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from .models import UserProfile, StudentProfile # استدعي موديلاتك

# هنستخدم الإشارة الخاصة بـ allauth بدل post_save
@receiver(user_signed_up)
def create_social_profile(request, user, sociallogin=None, **kwargs):
    
    # لو المتغير sociallogin موجود، معناه إن التسجيل ده جي من (Google/Facebook) ومش من الفورم العادية
    if sociallogin:
        
        # 1. بنعمله UserProfile ونديله رتبة طالب افتراضياً
        UserProfile.objects.get_or_create(
            user=user, 
            defaults={'role': 'student'}
        )
        
        # 2. بنعمله StudentProfile الخاص بيه
        StudentProfile.objects.get_or_create(user=user)