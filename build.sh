#!/bin/bash
set -e

pip install -r requirements.txt
python manage.py migrate

python - <<'PYEOF'
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'womenconnect.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()

username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')

print(f"DEBUG: username={username}, email={email}, password_len={len(password)}")

user, created = User.objects.get_or_create(username=username)
user.email = email
user.set_password(password)
user.is_staff = True
user.is_superuser = True
user.is_active = True
user.save()
print(f"{'CREATED' if created else 'UPDATED'}: {username} / {email}")
print(f"Staff={user.is_staff}, Super={user.is_superuser}, Active={user.is_active}")
PYEOF