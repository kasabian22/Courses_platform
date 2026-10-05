from django.urls import path
from . import views

app_name = 'courses' 
urlpatterns = [
    path('', views.subject_courses_list, name='subject_courses_list'),
    path('add-course/', views.add_course, name='add_course'),
    path('course/<slug:slug>/', views.course_detail, name='course_detail'),
    path('course/<slug:slug>/edit-course/', views.edit_course, name='edit_course'),
    path('course/<slug:slug>/add-module/', views.add_module, name='add_module'),
    path('course/<slug:course_slug>/<int:module_id>/view-module/', views.view_module, name='view_module'),
    path('course/<slug:slug>/enroll-course/', views.enroll_course, name='enroll_course'),
    path('course/<slug:slug>/module/<int:module_id>/content/<str:model_name>/create', views.content_create_update, name='content_create_update'),
]
