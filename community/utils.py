# community/utils.py
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail

def send_verification_email(request, user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    domain = get_current_site(request).domain

    link = f"http://{domain}/verify/{uid}/{token}/"

    send_mail(
        subject="Verify your WomenConnect account 💕",
        message=f"Click the link to verify your account:\n{link}",
        from_email=None,
        recipient_list=[user.email],
    )
