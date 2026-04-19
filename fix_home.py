import re

with open('community/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the entire home function body
old = '''def home(request):
    categories = Category.objects.all()'''

new = '''def home(request):
    categories = Category.objects.all()
    cutoff = timezone.now() - timezone.timedelta(hours=48)
    recent_posts = list(Post.objects.filter(created_at__gte=cutoff).select_related('author', 'category', 'author__userprofile').order_by('-created_at')[:10])
    for post in recent_posts:
        post.reply_count = post.replies.count()
    older_posts = list(Post.objects.filter(created_at__lt=cutoff).select_related('author', 'category', 'author__userprofile').order_by('-created_at')[:10])
    for post in older_posts:
        post.reply_count = post.replies.count()'''

# Remove the old block after categories line
pattern = r'def home\(request\):\n    categories = Category\.objects\.all\(\)\n.*?recent_posts = .*?\[:10\]\n    older_posts = .*?\[:10\]'
replacement = new

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('community/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('DONE')
