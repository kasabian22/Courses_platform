from django.contrib import admin
from .models import InstructorProfile, StudentProfile, UserProfile

# Register your models here.

@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'contact_email', 'header')
    search_fields = ('user__username', 'bio', 'contact_email', 'header')


admin.site.register(StudentProfile)
admin.site.register(UserProfile)