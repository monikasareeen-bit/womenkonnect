import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'womenkonnect.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

email = os.environ.get('DJANGO_SUPERUSER_EMAIL')

try:
    user = User.objects.get(email=email)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print(f"✅ {email} is now a superuser!")
except User.DoesNotExist:
    print("❌ User not found.")