from django.contrib import admin
from .models import Enrollment, Progress, Review, Subject, Course, Module, Content, Video
from django.db.models import Avg, Count

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
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

admin.site.register(Module)
admin.site.register(Content)
admin.site.register(Video)
admin.site.register(Progress)
admin.site.register(Enrollment)
