from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('sign-up/', views.sign_up, name='sign_up'),
    path('sign-out/', views.sign_out, name='sign_out'),
    path('sign-in/', views.sign_in, name='sign_in'),
    path('view-profile/', views.view_profile, name='view_profile'),
    path('edit-instructor-profile/', views.edit_instructor_profile, name='edit_instructor_profile'),
    path('edit-student-profile/', views.edit_student_profile, name='edit_student_profile'),
    path('upgrade-instructor/', views.upgrade_to_instructor, name='upgrade_instructor'),
    path('instructor/<int:instructor_id>/', views.public_instructor_profile, name='public_instructor_profile')
]
