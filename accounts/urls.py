from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('sign-up/', views.sign_up, name='sign_up'),
    path('sign-out/', views.sign_out, name='sign_out'),
    path('sign-in/', views.sign_in, name='sign_in'),
    path('change-password/', views.change_password, name='change_password'),
    path('view-profile/', views.view_profile, name='view_profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('upgrade-instructor/', views.upgrade_to_instructor, name='upgrade_instructor'),
    path('send-instructor-request/', views.send_instructor_request, name='send_instructor_request'),
    path('instructor/<int:instructor_id>/', views.public_instructor_profile, name='public_instructor_profile'),
    path('dismiss-instructor-request/', views.dismiss_instructor_request, name='dismiss_instructor_request'),
]
