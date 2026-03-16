#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate

python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()

username="admin"
email="monikasareena@gmail.com"
password="connectsatija"

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username,email,password)
    print("Admin created successfully")
else:
    print("Admin already exists")
END
