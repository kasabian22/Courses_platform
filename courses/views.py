from django.shortcuts import redirect, render, get_object_or_404
from .forms import CourseForm, TextForm, FileForm, VideoForm, ImageForm, ModuleForm
from .models import Subject, Course
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseForbidden
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


    return render(request, 'courses/course_detail.html', {
        'detail': course
    })


@permission_required('courses.add_course', raise_exception=True)
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
        'course': course
    })


def enroll_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.user.is_authenticated:
        course.students.add(request.user)
        messages.success(request, 'You have successfully enrolled in this course')
        return redirect('courses:course_detail', slug=course.slug)
    else:
        messages.error(request, 'You need to sign in to enroll in courses.')
        return redirect('accounts:sign_in')
    