from django.contrib import admin
from .models import Enrollment, Progress, Review, Subject, Course, Module, Content, Video

@admin.register(Subject)
class Subject(admin.ModelAdmin):
    list_display = ['title', 'slug']
    # 'slug' inherits from 'title' automatically.
    prepopulated_fields = {'slug': ('title',)}

class ModuleInline(admin.StackedInline):
    model = Module 

# 1. Inline to show and manage enrolled students inside the Course admin page
class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 1

# 2. Inline to show and manage course reviews inside the Course admin page
class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0  # Set to 0 so it only shows existing reviews without empty rows

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    # Display all model fields, properties, and custom M2M methods in the outer table
    list_display = [
        'title', 
        'owner', 
        'subject', 
        'status', 
        'level', 
        'language', 
        'time_to_complete', 
        'bestseller_badge', 
        'students_count', 
        'reviews_count', 
        'average_rating', 
        'date_created',
        'display_students',
        'display_wishlist',
    ]
    
    # Add useful filters on the right sidebar
    list_filter = ['status', 'level', 'language', 'subject', 'date_created']
    
    # Enable search by title, overview, or owner's username
    search_fields = ['title', 'overview', 'owner__username']
    
    # Show auto-generated fields and @property methods inside the Course edit form
    readonly_fields = [
        'slug', 
        'date_created', 
        'students_count', 
        'reviews_count', 
        'average_rating'
    ]
    
    # Nice dual-box selector for the standard ManyToManyField (wishlist)
    filter_horizontal = ['wishlist']
    
    # Attach Modules, Enrollments (students), and Reviews tables inside the Course page
    inlines = [ModuleInline, EnrollmentInline, ReviewInline]

    def get_queryset(self, request):
        # Optimize database queries by fetching related objects in advance
        return super().get_queryset(request).select_related('owner', 'subject').prefetch_related('students', 'wishlist', 'review_details')

    def display_students(self, obj):
        # Format enrolled students' usernames as a comma-separated string
        students = obj.students.all()
        if students.exists():
            return ", ".join([student.username for student in students])
        return "No students"
    display_students.short_description = 'Enrolled Students'

    def display_wishlist(self, obj):
        # Format wishlisted users' usernames as a comma-separated string
        users = obj.wishlist.all()
        if users.exists():
            return ", ".join([user.username for user in users])
        return "Empty"
    display_wishlist.short_description = 'Wishlisted By'

admin.site.register(Module)
admin.site.register(Content)
admin.site.register(Video)
admin.site.register(Progress)
admin.site.register(Enrollment)
