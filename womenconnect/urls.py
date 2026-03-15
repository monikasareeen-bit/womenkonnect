from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView

urlpatterns = [
    path('sugaradmin/', admin.site.urls),
    path('', include('community.urls')),
    path('favicon.ico', RedirectView.as_view(url='/static/community/images/womenkonnect-logo.svg', permanent=True)),

    path('password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='community/auth/password_reset.html'
        ),
        name='password_reset'
    ),
    path('password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='community/auth/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path('reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='community/auth/password_reset_confirm.html'
        ),
        name='password_reset_confirm'
    ),
    path('reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='community/auth/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
]

# Serve media files (PythonAnywhere handles via static file mapping in production)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Error handlers
handler404 = 'community.views.handler404'
handler500 = 'community.views.handler500'
handler403 = 'community.views.handler403'