from django.shortcuts import redirect

# Paths matched by PREFIX (path.startswith(url)) — safe to be broad here
# because every "write" action under these prefixes (create/edit/delete/
# like/reply/report/etc) already has its own @login_required decorator
# on the view itself, so exempting the prefix at the middleware level
# doesn't remove that protection — it just stops blocking the public
# read-only pages (post detail, category listing) that live under the
# same prefix.
EXEMPT_PREFIXES = [
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
    '/accounts/',
    '/about/',
    '/contact/',
    '/category/',
    '/post/',
    '/search/',
    #'/admin/',
]

# Paths matched EXACTLY. Home ('/') can't go in EXEMPT_PREFIXES above,
# because path.startswith('/') would be True for every single URL on
# the site and exempt everything.
EXEMPT_EXACT = [
    '/',
]


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            path = request.path
            exempt = path in EXEMPT_EXACT or any(path.startswith(url) for url in EXEMPT_PREFIXES)
            if not exempt:
                return redirect(f"/login/?next={path}")
        return self.get_response(request)