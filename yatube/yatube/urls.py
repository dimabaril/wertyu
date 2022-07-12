# yatube/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# хотя теория говорит что 403 здесь не надо
# но пайтест ругается
handler403 = 'core.views.csrf_failure'

handler404 = 'core.views.page_not_found'
handler500 = 'core.views.server_trouble'

urlpatterns = [
    path('admin/', admin.site.urls),
    # импорт правил из приложения posts
    path('', include('posts.urls', namespace='posts')),
    # авторизация
    path('auth/', include('users.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    path('about/', include('about.urls', namespace='about')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
