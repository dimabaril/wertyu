# core/views.py
from django.shortcuts import render


def page_not_found(request, exception):
    """Page 404."""
    # Переменная exception содержит отладочную информацию;
    # выводить её в шаблон пользовательской страницы 404 мы не станем
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def server_trouble(request, *args, **kwargs):
    """Page 500."""
    # Переменная exception содержит отладочную информацию;
    # выводить её в шаблон пользовательской страницы 500 мы не станем
    return render(request, 'core/500.html', {'path': request.path}, status=500)


def csrf_failure(request, reason=''):
    """Page 403."""
    return render(request, 'core/403csrf.html')
