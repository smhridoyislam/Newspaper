from .models import Category


def categories_processor(request):
    """Make categories available to all templates"""
    return {
        'all_categories': Category.objects.filter(is_active=True).order_by('order'),
    }
