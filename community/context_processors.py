from django.contrib.auth.models import User
from django.core.cache import cache
from .models import Post, Category


def community_stats(request):
    total_posts = cache.get('total_posts')
    total_members = cache.get('total_members')
    if total_posts is None:
        total_posts = Post.objects.count()
        cache.set('total_posts', total_posts, 300)
    if total_members is None:
        total_members = User.objects.count()
        cache.set('total_members', total_members, 300)
    return {
        'total_posts': total_posts,
        'total_members': total_members,
    }


def global_categories(request):
    categories = cache.get('global_categories')
    if categories is None:
        categories = list(Category.objects.all())
        cache.set('global_categories', categories, 600)
    return {'categories': categories}