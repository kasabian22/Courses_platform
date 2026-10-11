from django.contrib import admin
from .models import InstructorProfile, StudentProfile, UserProfile
from django.contrib.auth.admin import UserAdmin

# Register your models here.

@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'contact_email', 'header')
    search_fields = ('user__username', 'bio', 'contact_email', 'header')

class StudentProfileAdmin(admin.ModelAdmin):
    fields = ('user', 'photo', 'bio', 'full_name', 'is_eligible_for_instructor')
    list_display = ('user', 'is_eligible_for_instructor')

admin.site.register(StudentProfile, StudentProfileAdmin)

# admin.site.register(StudentProfile)
admin.site.register(UserProfile)