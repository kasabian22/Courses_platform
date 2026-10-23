from django.contrib import admin
from .models import Enrollment, Progress, Review, Subject, Course, Module, Content, Video
from django.db.models import Avg, Count

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug']
    readonly_fields = ['slug']  # Shows the slug without asking you to type it!

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
    # ... (keep list_display, list_filter, search_fields, readonly_fields, filter_horizontal, inlines as they are)

    def get_queryset(self, request):
        # Optimize queries AND annotate counts/ratings so @property methods don't trigger N+1 queries
        return super().get_queryset(request).select_related(
            'owner', 'subject'
        ).prefetch_related(
            'students', 'wishlist'
        ).annotate(
            enrolled_students_count=Count('students', distinct=True),
            annotated_reviews_count=Count('review_details', distinct=True),
            annotated_avg_rating=Avg('review_details__rating')
        )

    def display_students(self, obj):
        # Iterate directly over prefetched cache in memory without calling .exists()
        names = [student.username for student in obj.students.all()]
        return ", ".join(names) if names else "No students"
    display_students.short_description = 'Enrolled Students'

    def display_wishlist(self, obj):
        # Iterate directly over prefetched cache in memory without calling .exists()
        names = [user.username for user in obj.wishlist.all()]
        return ", ".join(names) if names else "Empty"
    display_wishlist.short_description = 'Wishlisted By'

@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    # Columns shown in the list table
    list_display = ['user', 'get_course', 'module', 'is_completed', 'completed_at']
    
    # Allow toggling completion status directly from the list view
    list_editable = ['is_completed']
    
    # Filters in the right sidebar
    list_filter = ['is_completed', 'module__course', 'completed_at']
    
    # Search bar supporting student, module title, and course title
    search_fields = [
        'user__username',
        'user__email',
        'module__title',
        'module__course__title',
    ]
    
    # Prevent N+1 SQL queries by joining foreign keys upfront
    list_select_related = ['user', 'module', 'module__course']
    
    # completed_at uses auto_now=True, so it must be readonly to be displayed in the edit form
    readonly_fields = ['completed_at']
    
    # Date navigation bar at the top & sort most recent first
    date_hierarchy = 'completed_at'
    ordering = ['-completed_at']

    # Custom column to show which course the module belongs to
    @admin.display(description='Course', ordering='module__course__title')
    def get_course(self, obj):
        return obj.module.course.title



# Inline to view and manage contents (videos, text, images, files) inside a module
class ContentInline(admin.TabularInline):
    model = Content
    extra = 0
    readonly_fields = ['item']  # Displays the linked content item (e.g. video or text title)


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    # Columns in the module list table
    list_display = ['title', 'course', 'contents_count', 'date_created']
    
    # Filter sidebar by Course and Date created
    list_filter = ['course', 'date_created']
    
    # Search bar across module title, description, and parent course name
    search_fields = ['title', 'description', 'course__title']
    
    # Read-only timestamp
    readonly_fields = ['date_created']
    
    # Group modules together by course and sort by ID
    ordering = ['course', 'id']
    date_hierarchy = 'date_created'
    
    # Show related contents directly inside the module view
    inlines = [ContentInline]

    def get_queryset(self, request):
        # Optimize queries by joining course and annotating total contents in one query
        return super().get_queryset(request).select_related(
            'course'
        ).annotate(
            annotated_contents_count=Count('contents')
        )

    # Custom column showing the count of content items (sortable)
    @admin.display(description='Total Contents', ordering='annotated_contents_count')
    def contents_count(self, obj):
        return obj.annotated_contents_count



admin.site.register(Content)
admin.site.register(Video)
admin.site.register(Enrollment)
