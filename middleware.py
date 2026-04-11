from django.shortcuts import redirect
from django.conf import settings

EXEMPT_URLS = [
    '/accounts/login/',
    '/accounts/logout/',
    '/verify/',           # email activation links
    '/activate/',         # your activation view
    '/register/',
    '/login/',
    '/forgot-password/',
    '/password-reset/',
    '/reset/',
    '/password-reset-confirm/',
    '/robots.txt',
    '/sitemap.xml',
    '/favicon.ico',
    '/static/',
    '/media/',
]

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            path = request.path
            exempt = any(path.startswith(url) for url in EXEMPT_URLS)
            if not exempt:
                return redirect(f"{settings.LOGIN_URL}?next={path}")
        return self.get_response(request)