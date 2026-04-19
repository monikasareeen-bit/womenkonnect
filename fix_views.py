content = open('community/views.py', 'r', encoding='utf-8').read()

old = "recent_posts = Post.objects.select_related('author', 'category', 'author__userprofile').prefetch_related('likes').filter(created_at__gte=cutoff).annotate(reply_count=Count('replies', distinct=True)).order_by('-created_at')[:10]"
new = "recent_posts = Post.objects.select_related('author', 'category', 'author__userprofile').filter(created_at__gte=cutoff).annotate(reply_count=Count('replies', distinct=True)).order_by('-created_at')[:10]"
content = content.replace(old, new)

old2 = "older_posts = Post.objects.select_related('author', 'category', 'author__userprofile').prefetch_related('likes').filter(created_at__lt=cutoff).annotate(reply_count=Count('replies', distinct=True)).order_by('-created_at')[:10]"
new2 = "older_posts = Post.objects.select_related('author', 'category', 'author__userprofile').filter(created_at__lt=cutoff).annotate(reply_count=Count('replies', distinct=True)).order_by('-created_at')[:10]"
content = content.replace(old2, new2)

open('community/views.py', 'w', encoding='utf-8').write(content)
print('DONE')
