python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()

username="admin"
password="admin123"

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username,"admin@example.com",password)
    print("Admin created")
else:
    print("Admin already exists")
END