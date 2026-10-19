import uuid
from django.utils.text import slugify

def generate_unique_slug(instance, title):
    base_slug = slugify(title)
    
    # Fallback in case slugify returns an empty string
    if not base_slug:
        base_slug = f"course-{uuid.uuid4().hex[:8]}"
        
    slug = base_slug
    ModelClass = instance.__class__
    counter = 1
    
    # Exclude the current instance in case we are updating an existing course
    while ModelClass.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
        
    return slug