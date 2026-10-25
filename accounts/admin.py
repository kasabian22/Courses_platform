from django.contrib import admin
from .models import InstructorProfile, InstructorRequest, StudentProfile, UserProfile


@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'contact_email', 'country', 'education')
    search_fields = ('user__username', 'full_name', 'bio', 'contact_email', 'header')
    list_filter = ('education', 'country')


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    # Include all BaseProfile fields alongside student-specific fields
    fields = (
        'user', 'full_name', 'photo', 'bio',
        'country', 'education', 'primary_language_spoken',
        'linkedin', 'github', 'facebook',
        'display_enrolled_courses'
    )
    readonly_fields = ('display_enrolled_courses',)
    list_display = ('user', 'full_name', 'country', 'display_enrolled_courses')
    list_filter = ('education', 'country')
    search_fields = ('user__username', 'full_name', 'user__email')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('user__enrolled_courses')

    def display_enrolled_courses(self, obj):
        # Iterate over prefetched queryset directly in memory without calling .exists()
        courses = obj.user.enrolled_courses.all()
        if courses:
            return ", ".join([course.title for course in courses])
        return "No courses"

    display_enrolled_courses.short_description = 'Enrolled Courses'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')




@admin.action(description='Approval of specific requests and account upgrade')
def approve_requests(modeladmin, request, queryset):
    for req in queryset:
        req.status = 'approved'
        req.is_seen = False  # So that the acceptance message appears to him when he opens the website.
        req.save()
        


@admin.action(description='Reject specific requests')
def reject_requests(modeladmin, request, queryset):
    queryset.update(status='rejected', is_seen=False)

@admin.register(InstructorRequest)
class InstructorRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'is_seen', 'created_at']
    
    list_filter = ['status', 'is_seen', 'created_at']
    search_fields = ['user__username', 'user__email']
    
    actions = [approve_requests, reject_requests]
    
    readonly_fields = ['created_at']