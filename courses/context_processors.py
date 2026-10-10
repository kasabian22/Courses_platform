from .models import Subject

def subject_categories(request):
    return {'all_subjects': Subject.objects.all()}