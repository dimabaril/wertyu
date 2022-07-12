from django.utils import timezone


def get_year(request):
    """Добавляет переменную с текущим годом."""
    return {
        'year': timezone.now().year
    }
