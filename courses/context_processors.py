from django.db.models import Case, When
from .models import Subject

def subject_categories(request):
    # Orders all subjects alphabetically by title, but pushes 'other' to the very end
    subjects = Subject.objects.order_by(
        Case(When(slug='other', then=1), default=0),
        'title'
    )
    return {'all_subjects': subjects}
