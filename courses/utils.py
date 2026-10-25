import re
import uuid
from unidecode import unidecode
from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator

def extract_smart_base_slug(title):
    """
    Apply the 4 smart rules to generate a base slug from a course title:
    1. Pure English/ASCII -> standard slugify.
    2. Mixed Arabic + meaningful English phrase (2+ words of 3+ letters) -> English + numbers only.
    3. Pure Arabic / other languages -> transliterate everything via unidecode.
    4. Arabic + dependent numbers (e.g., Part 3) or short English letters (e.g., C, Ch 1) -> transliterate everything together.
    """
    if not title:
        return ""

    # Check if the title contains any non-ASCII characters (like Arabic)
    has_non_ascii = bool(re.search(r"[^\x00-\x7F]", title))

    if not has_non_ascii:
        # Pure English/ASCII title
        return slugify(title)

    # Extract meaningful English words (3 or more letters)
    meaningful_english_words = re.findall(r"[a-zA-Z]{3,}", title)

    if len(meaningful_english_words) >= 2:
        # Rule 1: Meaningful English phrase exists -> extract all English words and numbers only
        english_and_numbers = re.findall(r"[a-zA-Z0-9]+", title)
        base_slug = slugify(" ".join(english_and_numbers))
    else:
        # Rules 2, 3, 4: Pure Arabic, or Arabic with numbers/short dependent English tokens
        base_slug = slugify(unidecode(title))

    return base_slug


def generate_unique_slug(instance_or_model, title="", custom_slug="", exclude_pk=None):
    """
    Generate a guaranteed non-empty, unique slug for a Course.
    Prioritizes custom_slug if provided; otherwise derives it from title.
    """
    # If a custom slug is provided by the user, sanitize it via unidecode + slugify
    if custom_slug and custom_slug.strip():
        base_slug = slugify(unidecode(custom_slug.strip()))
    else:
        base_slug = extract_smart_base_slug(title)

    # Ultimate fallback if input was only symbols like "???" generate random slug
    if not base_slug:
        base_slug = f"course-{uuid.uuid4().hex[:8]}"

    # Determine the Model class and the primary key to exclude (if he wants to update it)
    if isinstance(instance_or_model, models.Model):
        ModelClass = instance_or_model.__class__
        exclude_pk = instance_or_model.pk
    else:
        ModelClass = instance_or_model

    qs = ModelClass.objects.all()
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)


    # Truncate base_slug to 240 chars so appending '-1', '-2' never exceeds max_length=250 of the slug in models.py
    base_slug = base_slug[:240].strip('-')
    

    # Fetch all matching slugs in one single SQL query
    existing_slugs = set(
        qs.filter(
            models.Q(slug=base_slug) | models.Q(slug__regex=rf'^{re.escape(base_slug)}-\d+$')
        ).values_list('slug', flat=True)
    )
    if base_slug not in existing_slugs:
        return base_slug
    
    counter = 1
    while f"{base_slug}-{counter}" in existing_slugs:
        counter += 1
    
    return f"{base_slug}-{counter}"

    # while qs.filter(slug=slug).exists():
    #     slug = f"{base_slug}-{counter}"
    #     counter += 1




# =================================================================================================================== #

def paginate_queryset(request, queryset, per_page=9):
    """
    A helper function for paginating any QuerySet
    """
    # Initialize Paginator: Show 9 courses per page (3 rows x 3 columns)
    paginator = Paginator(queryset, per_page)

    # Get the requested page number from the URL query string (e.g., ?page=2)
    page_number = request.GET.get('page', 1)

    # get_page() safely handles invalid strings (like ?page=abc) or out-of-range numbers
    return paginator.get_page(page_number)



# =================================================================================================================== #


