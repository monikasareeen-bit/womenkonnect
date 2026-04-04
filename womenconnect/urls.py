# womenconnect/urls.py

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from django.utils import timezone

from community.models import Post, Category


# ── Sitemaps ──────────────────────────────────────────────────────────────────
# We write custom Sitemap classes instead of GenericSitemap so we can safely
# control get_absolute_url, lastmod, and changefreq without touching models.

from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticSitemap(Sitemap):
    priority   = 1.0
    changefreq = "weekly"

    def items(self):
        return ["home", "about", "contact"]

    def location(self, item):
        return reverse(item)


class PostSitemap(Sitemap):
    priority   = 0.8
    changefreq = "daily"

    def items(self):
        return Post.objects.all().order_by("-created_at")

    def lastmod(self, obj):
        # Use updated_at if it exists, otherwise fall back to created_at
        return getattr(obj, "updated_at", None) or obj.created_at

    def location(self, obj):
        return reverse("post_detail", args=[obj.pk])


class CategorySitemap(Sitemap):
    priority   = 0.6
    changefreq = "weekly"

    def items(self):
        return Category.objects.all()

    def location(self, obj):
        # Adjust if your category URL name / slug field is different
        try:
            return reverse("category_detail", args=[obj.slug])
        except Exception:
            # Fallback: if no category_detail URL exists yet, skip by returning home
            return reverse("home")


sitemaps = {
    "static":     StaticSitemap,
    "posts":      PostSitemap,
    "categories": CategorySitemap,
}


# ── robots.txt ────────────────────────────────────────────────────────────────
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "",
        "# No value crawling these — they're dynamic/private",
        "Disallow: /sugaradmin/",
        "Disallow: /profile/",
        "Disallow: /search/",
        "Disallow: /verify/",
        "Disallow: /accounts/",
        "Disallow: /password-reset/",
        "Disallow: /reset/",
        "",
        "Sitemap: https://womenkonnect.co.in/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


# ── URL patterns ──────────────────────────────────────────────────────────────
urlpatterns = [
    path("sugaradmin/", admin.site.urls),
    path("", include("community.urls")),

    # Favicon
    path(
        "favicon.ico",
        RedirectView.as_view(
            url="/static/community/images/womenkonnect-logo.svg",
            permanent=True,
        ),
    ),

    # SEO
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("robots.txt", robots_txt),

    # Password reset flow
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="community/auth/password_reset.html"
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="community/auth/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="community/auth/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="community/auth/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ── Error handlers ────────────────────────────────────────────────────────────
handler404 = "community.views.handler404"
handler500 = "community.views.handler500"
handler403 = "community.views.handler403"