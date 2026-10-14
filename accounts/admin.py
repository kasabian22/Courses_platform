from django.contrib import admin
from .models import InstructorProfile, StudentProfile, UserProfile
from courses.models import Enrollment
from django.contrib.auth.admin import UserAdmin

# Register your models here.

@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'contact_email', 'header')
    search_fields = ('user__username', 'bio', 'contact_email', 'header')

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    # Display the custom method inside the form as a read-only field
    fields = ('user', 'photo', 'bio', 'full_name', 'is_eligible_for_instructor', 'display_enrolled_courses')
    readonly_fields = ('display_enrolled_courses',)
    
    # Columns displayed in the outer admin table
    list_display = ('user', 'is_eligible_for_instructor', 'display_enrolled_courses')

    def get_queryset(self, request):
        # Prefetch from the user's actual enrolled_courses relation
        return super().get_queryset(request).select_related('user').prefetch_related('user__enrolled_courses')

    def display_enrolled_courses(self, obj):
        # Fetch courses from the User's actual Enrollment relation
        courses = obj.user.enrolled_courses.all()
        if courses.exists():
            return ", ".join([course.title for course in courses])
        return "No courses"

    # Set column and field title in admin
    display_enrolled_courses.short_description = 'Enrolled Courses'


# admin.site.register(StudentProfile)
admin.site.register(UserProfile)