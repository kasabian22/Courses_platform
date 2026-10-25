# (Global Template Data)
# A Context Processor is a Python function that takes request as an argument and returns a Python dictionary. Django automatically merges this dictionary into every single template rendered with RequestContext across the entire website.

from django.core.cache import cache
from django.db.models import Case, When
from .models import Subject

CACHE_KEY = 'global_subject_categories'
CACHE_TIMEOUT = 60 * 60 * 24  # Cache for 24 hours (in seconds)

def subject_categories(request):
    # cache.get_or_set checks if 'global_subject_categories' is in cache.
    # If yes -> returns it instantly from RAM (0 database queries).
    # If no  -> runs the lambda, stores the result, and returns it.
    subjects = cache.get_or_set(
        CACHE_KEY,
        lambda: list(
            Subject.objects.order_by(
                Case(When(slug='other', then=1), default=0),
                'title'
            )
        ),
        timeout=CACHE_TIMEOUT
    )
    return {'all_subjects': subjects}