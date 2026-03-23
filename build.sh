#!/bin/bash
set -e

pip install -r requirements.txt
python manage.py migrate

# Create or update superuser directly
python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()
import os

email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')

user, created = User.objects.get_or_create(username=username)
user.email = email
user.is_staff = True
user.is_superuser = True
user.is_active = True
user.set_password(password)
user.save()

if created:
    print(f"✅ NEW superuser created: {username}")
else:
    print(f"✅ EXISTING user updated: {username}")

print(f"   Email: {user.email}")
print(f"   is_staff: {user.is_staff}")
print(f"   is_superuser: {user.is_superuser}")
print(f"   is_active: {user.is_active}")
EOF
