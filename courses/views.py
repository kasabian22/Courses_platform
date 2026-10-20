from django.apps import apps
from django.shortcuts import redirect, render, get_object_or_404
from unidecode import unidecode

from .utils import extract_smart_base_slug, generate_unique_slug
from .forms import CourseForm, TextForm, FileForm, VideoForm, ImageForm, ModuleForm, ReviewForm
from .models import Content, Enrollment, Module, Progress, Review, Subject, Course
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_POST
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.utils.text import slugify
from django.contrib import messages
from django.db.models import Count, Prefetch, Q


def subject_courses_list(request):
    # get all the courses and the subjects with on query instead of two.
    courses = Course.objects.filter(status=Course.Status.AVAILABLE).select_related(
        'owner', 'owner__instructors_profiles'
    ).annotate(
        enrolled_students_count=Count('students', distinct=True)
    )
    subjects = Subject.objects.prefetch_related(
        Prefetch('courses', queryset=courses)
    )

    return render(request, 'courses/subject_course_list.html', {
        'subjects': subjects
    })


def category_courses(request, subject_slug):
    subject = get_object_or_404(Subject, slug=subject_slug)
    courses = Course.objects.filter(subject=subject, status=Course.Status.AVAILABLE).select_related(
        'owner', 'owner__instructors_profiles'
    ).annotate(
        enrolled_students_count=Count('students', distinct=True)
    )
    
    return render(request, 'courses/category_courses.html', {
        'subject': subject,
        'courses': courses
    })

# you can use id instead of slug.
def course_detail(request, slug):
    course = get_object_or_404(
        Course.objects.select_related('owner', 'owner__instructors_profiles', 'subject').prefetch_related('modules'), 
        slug=slug
    )
    reviews = Review.objects.filter(course=course).select_related(
        'user', 'user__students_profiles', 'user__instructors_profiles'
    ).order_by('-created_at')
    
    enrollment = None
    has_reviewed = False
    
    # check if the user enrolled and if the user has already reviewed the course
    if request.user.is_authenticated:
        enrollment = Enrollment.objects.filter(user=request.user, course=course).first()
        if enrollment:
            has_reviewed = Review.objects.filter(course=course, user=request.user).exists()
    
    return render(request, 'courses/course_detail.html', {
        'detail': course,
        'enrollment': enrollment,
        'reviews': reviews,
        'has_reviewed': has_reviewed
    })


def search_courses(request):
    # Get the search query from the URL (e.g., ?q=python), default to empty string
    query = request.GET.get('q', '')
    
    courses = Course.objects.filter(status=Course.Status.AVAILABLE).select_related(
        'owner', 'owner__instructors_profiles'
    ).annotate(
        enrolled_students_count=Count('students', distinct=True)
    )
    
    if query:
        # Search in course title OR course overview OR subject title OR course owner
        courses = courses.filter(
            Q(title__icontains=query) | 
            Q(overview__icontains=query) |
            Q(subject__title__icontains=query)|
            Q(owner__username__icontains=query)
        ).distinct() 

    return render(request, 'courses/search_results.html', {
        'query': query,
        'courses': courses
    })

@login_required
@permission_required('courses.add_content', raise_exception=True)
def content_create_update(request, slug, module_id, model_name, id=None):
    forms_map = {
        'text': TextForm, 
        'video': VideoForm, 
        'image': ImageForm, 
        'file': FileForm
    }
    
    # Ensure the module belongs to a course owned by the current user
    module = get_object_or_404(Module, id=module_id, course__owner=request.user, course__slug=slug)
    
    if model_name not in forms_map:
        return HttpResponseBadRequest()

    form_class = forms_map[model_name]
    
    # Dynamically fetch the model class (Text, Video, Image, or File) to get the existing item if updating
    model_class = apps.get_model(app_label='courses', model_name=model_name)
    obj = None
    
    if id:
        # Fetch the existing item owned by the instructor for updating
        obj = get_object_or_404(model_class, id=id, owner=request.user)

    if request.method == 'POST':
        # Pass 'instance=obj' so Django updates the existing item if 'obj' is not None
        form = form_class(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            item = form.save(commit=False)
            item.owner = request.user
            item.save()
            
            # Only create a new Content link if we are creating a new item (not updating)
            if not id:
                Content.objects.create(
                    module=module,
                    item=item
                )
            # Redirect back to the module view so the instructor sees the new/updated content immediately
            return redirect("courses:view_module", course_slug=module.course.slug, module_id=module.id)
    else:
        # Pre-fill the form with the existing item's data if editing
        form = form_class(instance=obj)

    return render(request, "courses/add_content.html", {
        "form": form,
        "model_name": model_name,
        "module": module,
        "object": obj,  # Useful if you want to show "Edit" vs "Add" in add_content.html
    })


@login_required
def delete_content(request, course_slug, module_id, content_id):
    # Ensure the content belongs to the specified module and the course is owned by the current user
    content = get_object_or_404(
        Content, 
        id=content_id, 
        module__id=module_id, 
        module__course__slug=course_slug, 
        module__course__owner=request.user
    )
    
    # Delete the actual item (Video, Text, Image, or File) and the Content relation
    content.item.delete()
    content.delete()
    
    return redirect("courses:view_module", course_slug, module_id)



@permission_required('courses.add_course', raise_exception=True)
@login_required(login_url='accounts:sign_up')
def add_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.owner = request.user
            course.save()
            return redirect('courses:subject_courses_list')
    else:
        form = CourseForm()

    return render(request, 'courses/add_course.html', {
        'form': form
    })


@login_required(login_url='accounts:sign_up')
@permission_required('courses.edit_course', raise_exception=True)
def edit_course(request, slug):
    course = get_object_or_404(Course, slug=slug, owner=request.user)
    form = CourseForm(instance=course)
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            return redirect('accounts:view_profile')
    return render(request, 'courses/edit_course.html', {
        'form': form,
        'course': course
    })



@login_required
def generate_slug_preview(request):
    """
    AJAX endpoint to preview and validate the course slug in real time.
    """
    title = request.GET.get('title', '').strip()
    custom_slug = request.GET.get('custom_slug', '').strip()
    course_id = request.GET.get('course_id')

    exclude_pk = int(course_id) if course_id and course_id.isdigit() else None

    if custom_slug:
        base_candidate = slugify(unidecode(custom_slug))
    else:
        base_candidate = extract_smart_base_slug(title)

    if not base_candidate:
        return JsonResponse({
            'slug': '',
            'is_valid': False,
            'was_modified_for_uniqueness': False,
            'message': 'Enter a valid title or slug'
        })

    final_slug = generate_unique_slug(
        Course,
        title=title,
        custom_slug=custom_slug,
        exclude_pk=exclude_pk
    )

    # Check if a counter (-1, -2) was appended because another course already took the base slug
    was_modified = (final_slug != base_candidate)

    return JsonResponse({
        'slug': final_slug,
        'is_valid': True,
        'was_modified_for_uniqueness': was_modified,
        'message': f"Available as: {final_slug}" if was_modified else "Slug is available ✓"
    })


@require_POST
@login_required
def delete_course(request, slug):
    course = get_object_or_404(Course, slug=slug, owner=request.user)
    course.delete()
    return redirect('accounts:view_profile')

@login_required
def review_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    enrollment = course.students.filter(id=request.user.id).exists()

    if not enrollment:
        messages.error(request, 'You must be enrolled in this course to leave a review.')
        return redirect('courses:course_detail', slug=course.slug)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.course = course
            review.user = request.user
            review.save()
            messages.success(request, 'Your review has been saved successfully!')
            return redirect('courses:course_detail', slug=course.slug)
    else:
        form = ReviewForm()
    
    return render(request, 'courses/review_course.html', {
        'form': form,
        'course': course,
        "type": "Add"
    })


def edit_review(request, slug):
    course = get_object_or_404(Course, slug=slug)
    review = get_object_or_404(Review, course=course, user=request.user)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            return redirect('courses:course_detail', slug=course.slug)
    else:
        form = ReviewForm(instance=review)
    
    return render(request, 'courses/review_course.html', {
        'form': form,
        'course': course,
        "type": "Edit"
    })


@require_POST
@login_required
def delete_review(request, slug):
    course = get_object_or_404(Course, slug=slug)
    review = get_object_or_404(Review, course=course, user=request.user)
    
    review.delete()
    messages.success(request, 'Your review has been deleted successfully!')
    return redirect('courses:course_detail', slug=course.slug)
    



@login_required
@permission_required('courses.add_module', raise_exception=True)
def add_module(request, slug):
    course = get_object_or_404(Course, slug=slug, owner=request.user)
    if request.method == 'POST':
        form = ModuleForm(request.POST)
        if form.is_valid():
            module = form.save(commit=False)
            module.course = course
            module.save()
            return redirect('courses:course_detail', slug=course.slug)
    else:
        form = ModuleForm()

    return render(request, 'courses/add_module.html', {
        'form': form,
        'course': course,
        'type': 'Add'
    })

def view_module(request, course_slug, module_id):
    course = get_object_or_404(Course, slug=course_slug)
    module_qs = Module.objects.prefetch_related('contents__item')
    module = get_object_or_404(module_qs, course=course, id=module_id)


    # Allow access if the user is the course owner OR an enrolled student
    is_owner = (course.owner == request.user)
    is_enrolled = course.students.filter(id=request.user.id).exists()

    if not is_enrolled and not is_owner:
        messages.error(request, 'You must be enrolled in this course to view its modules.')
        return redirect('courses:course_detail', slug=course.slug)

    has_reviewed = False
    if request.user.is_authenticated and is_enrolled:
        has_reviewed = Review.objects.filter(course=course, user=request.user).exists()

    is_completed = Progress.objects.filter(user=request.user, module=module, is_completed=True).exists()
    previous_module = course.modules.filter(id__lt=module.id).order_by('-id').first()
    next_module = course.modules.filter(id__gt=module.id).order_by('id').first()

    return render(request, "courses/view_module.html", {
        "course":course,
        "module":module,
        'is_completed': is_completed,
        'previous_module': previous_module,
        'next_module': next_module,
        'is_enrolled': is_enrolled,
        'has_reviewed': has_reviewed
    })

@login_required
@permission_required('courses.edit_module', raise_exception=True)
def edit_module(request, course_slug, module_id):
    course = get_object_or_404(Course, slug=course_slug, owner=request.user)
    module = get_object_or_404(Module, course=course, id=module_id)
    form = ModuleForm(instance=module)
    if request.method == 'POST':
            form = ModuleForm(request.POST, instance=module)
            if form.is_valid():
                form.save()
                return redirect('courses:course_detail', slug=course.slug)
    return render(request, 'courses/add_module.html', {
        'form': form,
        "type": "Edit",
        'course': course
    })


def delete_module(request, course_slug, module_id):
    course = get_object_or_404(Course, slug=course_slug, owner=request.user)
    module = get_object_or_404(Module, course=course, id=module_id)
    module.delete()
    return redirect('courses:course_detail', slug=course.slug)


@require_POST
@login_required
def complete_module(request, course_slug, module_id):
    module = get_object_or_404(Module, id=module_id)
    is_enrolled = module.course.students.filter(id=request.user.id).exists()
    
    if is_enrolled:
        Progress.objects.update_or_create(
            user=request.user,
            module=module,
            defaults={'is_completed': True}
        )
    return redirect('courses:view_module', module_id=module_id, course_slug=course_slug)

@require_POST
@login_required
def enroll_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if not course.students.filter(id=request.user.id).exists():
        course.students.add(request.user)
        messages.success(request, 'You have successfully enrolled in this course')
        return redirect('courses:course_detail', slug=course.slug)
    else:
        messages.info(request, 'You are already enrolled in this course.')
    
    return redirect('courses:course_detail', slug=course.slug)

@require_POST
@login_required
def unenroll_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if course.students.filter(id=request.user.id).exists():
        course.students.remove(request.user)
        messages.success(request, 'You have successfully unenrolled out of this course')
        return redirect('courses:course_detail', slug=course.slug)
    else:
        messages.info(request, 'You were not enrolled in this course.')
    
    return redirect('courses:course_detail', slug=course.slug)

@require_POST
@login_required
def toggle_wishlist(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if course.wishlist.filter(id=request.user.id).exists():
        course.wishlist.remove(request.user)
        messages.success(request, 'Course removed from wishlist')
        return redirect('courses:view_wishlist')
    else:
        course.wishlist.add(request.user)
        messages.success(request, 'Course added to wishlist')
        return redirect('courses:course_detail', slug=course.slug)

@login_required
def view_wishlist(request):
    wishlist = request.user.wishlist.select_related(
        'owner', 'owner__instructors_profiles'
    ).annotate(
        enrolled_students_count=Count('students', distinct=True)
    )
    return render(request, 'courses/wishlist.html', {'wishlist': wishlist})