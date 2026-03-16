python manage.py shell << END
from django.contrib.auth import get_user_model

User = get_user_model()

try:
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser("admin","admin@example.com","admin123")
        print("Admin created")
    else:
        print("Admin already exists")
except Exception as e:
    print("Admin creation skipped:", e)
END