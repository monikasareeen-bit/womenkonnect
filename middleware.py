from django.shortcuts import redirect
from django.conf import settings

EXEMPT_URLS = [
    '/login/',
    '/logout/',
    '/register/',
    '/activate/',
    '/password-reset/',
    '/password-reset-confirm/',
    '/robots.txt',
    '/sitemap.xml',
    '/favicon.ico',
    '/static/',
    '/media/',
    '/sugaradmin/',
]

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            path = request.path
            exempt = any(path.startswith(url) for url in EXEMPT_URLS)
            if not exempt:
                return redirect(f"/login/?next={path}")
        return self.get_response(request)