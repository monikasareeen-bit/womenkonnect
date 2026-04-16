from django.shortcuts import redirect

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
    '/admin/', 
]

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print(f">>> MIDDLEWARE RUNNING | path={request.path} | auth={request.user.is_authenticated}")
        if not request.user.is_authenticated:
            path = request.path
            exempt = any(path.startswith(url) for url in EXEMPT_URLS)
            print(f">>> EXEMPT={exempt}")
            if not exempt:
                print(f">>> REDIRECTING TO LOGIN")
                return redirect(f"/login/?next={path}")
        return self.get_response(request)