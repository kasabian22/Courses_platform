from django.contrib import admin
from .models import Progress, Subject, Course, Module, Content, Video

@admin.register(Subject)
class Subject(admin.ModelAdmin):
    list_display = ['title', 'slug']
    # 'slug' inherits from 'title' automatically.
    prepopulated_fields = {'slug': ('title',)}

class ModuleInline(admin.StackedInline):
    model = Module 

@admin.register(Course)
class Course(admin.ModelAdmin):
    list_display = ['title', 'subject', 'date_created', "status"]
    list_filter = ['date_created', 'subject']
    search_fields = ['title', 'overview']
    prepopulated_fields = {'slug': ('title',)}
    # when created a course automtically added under it's module.
    inlines = [ModuleInline]
    readonly_fields = ['slug']

admin.site.register(Module)
admin.site.register(Content)
admin.site.register(Video)
admin.site.register(Progress)
