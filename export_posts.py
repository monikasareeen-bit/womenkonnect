"""
Simple posts export script — avoids the server-side cursor issue that
Django's dumpdata hits with Supabase's connection pooler.

Run with:
    python manage.py shell < export_posts.py
"""
import json
from community.models import Post

posts = list(
    Post.objects.select_related('category').values(
        'id', 'title', 'content', 'category__name', 'created_at'
    )
)

for p in posts:
    p['created_at'] = str(p['created_at'])

with open('posts_export.json', 'w', encoding='utf-8') as f:
    json.dump(posts, f, ensure_ascii=False, indent=2)

print(f"Exported {len(posts)} posts to posts_export.json")