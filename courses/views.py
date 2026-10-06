from django.shortcuts import redirect, render, get_object_or_404
from .forms import CourseForm, TextForm, FileForm, VideoForm, ImageForm, ModuleForm
from .models import Content, Enrollment, Module, Progress, Subject, Course
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_POST
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.contrib import messages


def subject_courses_list(request):
    # get all the courses and the subjects with on query instead of two.
    subjects = Subject.objects.prefetch_related('courses').all()

    return render(request, 'courses/subject_course_list.html', {
        'subjects': subjects
    })


# you can use id instead of slug.
def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug)
    
    enrollment = None
    
    # check if the user enrolled
    if request.user.is_authenticated and course.students.filter(id=request.user.id).exists():
        enrollment = Enrollment.objects.filter(user=request.user, course=course).first()
    return render(request, 'courses/course_detail.html', {
        'detail': course,
        'enrollment': enrollment,
    })

@login_required
@permission_required('courses.add_content', raise_exception=True)
def content_create_update(request, slug, module_id, model_name):
    modules = {'text': TextForm, 'video': VideoForm, 'image': ImageForm, 'file': FileForm}
    module = get_object_or_404(Module, id=module_id, course__owner=request.user)
    if model_name in modules:
        form = modules[model_name]()
        if request.method == 'POST':
            form = modules[model_name](request.POST, request.FILES)
            if form.is_valid():
                item = form.save(commit=False)
                item.owner = request.user
                item.save()
                # ---------------
                Content.objects.create(
                    module=module,
                    item=item
                )
                return redirect("courses:course_detail", slug=module.course.slug)
                # ----------------

    else:
        return HttpResponseBadRequest()


    return render(request, "courses/add_content.html",{
        "form": form,
        "model_name": model_name
    })




# @permission_required('courses.add_course', raise_exception=True)
@login_required(login_url='accounts:sign_up')
def add_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
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


@login_required(login_url='accounts:sign_up')
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

    if not (is_owner or is_enrolled):
        return redirect('courses:course_detail', slug=course.slug)

    is_completed = Progress.objects.filter(user=request.user, module=module, is_completed=True).exists()
    previous_module = course.modules.filter(id__lt=module.id).order_by('-id').first()
    next_module = course.modules.filter(id__gt=module.id).order_by('id').first()

    return render(request, "courses/view_module.html", {
        "course":course,
        "module":module,
        'is_completed': is_completed,
        'previous_module': previous_module,
        'next_module': next_module,
    })

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
        "type": "Edit"
    })


@require_POST
@login_required
def complete_module(request, course_slug, module_id):
    module = get_object_or_404(Module, id=module_id)
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
    if request.user not in course.students.all():
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
    if request.user in course.students.all():
        course.students.remove(request.user)
        messages.success(request, 'You have successfully unenrolled out of this course')
        return redirect('courses:course_detail', slug=course.slug)
    else:
        messages.info(request, 'You were not enrolled in this course.')
    
    return redirect('courses:course_detail', slug=course.slug)