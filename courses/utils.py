from django.utils.text import slugify

def generate_unique_slug(instance, title):
    base_slug = slugify(title)
    unique_slug = base_slug
    
    # Get the model class dynamically 
    model_class = instance.__class__
    
    counter = 1
    
    # Keep checking the database; if the slug exists, append the counter to the base slug
    while model_class.objects.filter(slug=unique_slug).exists():
        unique_slug = f"{base_slug}-{counter}"
        
        counter += 1
        
    return unique_slug