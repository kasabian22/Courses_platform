from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('sign-up/', views.sign_up, name='sign_up'),
    path('verify-email/<str:uidb64>/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('sign-out/', views.sign_out, name='sign_out'),
    path('sign-in/', views.sign_in, name='sign_in'),
    path('change-password/', views.change_password, name='change_password'),
    path('view-profile/', views.view_profile, name='view_profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('upgrade-instructor/', views.upgrade_to_instructor, name='upgrade_instructor'),
    path('send-instructor-request/', views.send_instructor_request, name='send_instructor_request'),
    path('dismiss-instructor-request/', views.dismiss_instructor_request, name='dismiss_instructor_request'),
    path('instructor/<int:instructor_id>/', views.public_instructor_profile, name='public_instructor_profile'),

    # Password Reset Flow
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/emails/password_reset_email.html',
             subject_template_name='accounts/emails/password_reset_subject.txt',
             success_url=reverse_lazy('accounts:password_reset_done')
         ), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url=reverse_lazy('accounts:password_reset_complete')
         ), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]
