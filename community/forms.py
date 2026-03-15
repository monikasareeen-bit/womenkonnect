from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Post, Report
from .utils.profanity import check_profanity
import re


class ProfanityCleanMixin:
    """
    Mixin to add profanity checking to any form field.
    Usage: call self.check_profanity_on(value, 'Custom error message')
    or use the convenience wrapper clean_field_with_profanity(field_name, msg).
    """

    def check_profanity_on(self, value: str, error_msg: str = "Contains inappropriate language.") -> str:
        """
        Validate a *pre-cleaned* string value for profanity and return it.
        Raises ValidationError if profanity is detected.
        """
        if value and check_profanity(value):
            raise forms.ValidationError(error_msg)
        return value

    def clean_field_with_profanity(
        self,
        field_name: str,
        error_msg: str = "Contains inappropriate language.",
    ) -> str:
        """
        Pull cleaned_data[field_name], strip whitespace, check for profanity.
        Returns the stripped value (or '' if absent).

        NOTE: Prefer calling check_profanity_on() directly inside clean_<field>
        methods so that you control the exact value being validated (avoids
        double-read bugs when clean_<field> has already mutated the value).
        """
        value = self.cleaned_data.get(field_name, '')
        if isinstance(value, str):
            value = value.strip()
        return self.check_profanity_on(value, error_msg)


# ---------------------------------------------------------------------------
# Profile Form
# ---------------------------------------------------------------------------

class ProfileForm(forms.ModelForm, ProfanityCleanMixin):
    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'bio', 'location', 'website']
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Tell us about yourself...',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Mumbai, India',
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://yourwebsite.com',
            }),
        }

    def clean_bio(self):
        bio = self.cleaned_data.get('bio', '').strip()
        # Optional field — only validate if something was entered
        if not bio:
            return bio
        if len(bio) > 500:
            raise forms.ValidationError("Bio cannot exceed 500 characters.")
        return self.check_profanity_on(bio, "Your bio contains inappropriate language.")

    def clean_location(self):
        location = self.cleaned_data.get('location', '').strip()
        if not location:
            return location
        if len(location) > 100:
            raise forms.ValidationError("Location cannot exceed 100 characters.")
        return self.check_profanity_on(location, "Your location contains inappropriate language.")

    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        if picture and hasattr(picture, 'content_type'):
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if picture.content_type not in allowed_types:
                raise forms.ValidationError("Only JPEG, PNG, GIF, and WebP images are allowed.")
            if picture.size > 2 * 1024 * 1024:  # 2 MB
                raise forms.ValidationError("Profile picture must be under 2MB.")
        return picture


# ---------------------------------------------------------------------------
# Registration / Auth Forms
# ---------------------------------------------------------------------------

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()

        if not re.match(r'^[A-Za-z0-9_]+$', username):
            raise forms.ValidationError(
                "Username can only contain letters, numbers, and underscores."
            )
        if len(username) < 3:
            raise forms.ValidationError("Username must be at least 3 characters long.")
        if len(username) > 30:
            raise forms.ValidationError("Username cannot exceed 30 characters.")

        return username


class EmailAuthenticationForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your email',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password'})
    )

    def clean_email(self):
        return self.cleaned_data.get('email', '').strip().lower()


# ---------------------------------------------------------------------------
# Post Form
# ---------------------------------------------------------------------------

class PostForm(forms.ModelForm, ProfanityCleanMixin):
    class Meta:
        model = Post
        fields = ['title', 'content', 'category']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter a clear, descriptive title',
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Share your thoughts...',
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_title(self):
        # BUG FIX: always operate on one local variable, not re-reading from cleaned_data
        title = self.cleaned_data.get('title', '').strip()
        if len(title) < 5:
            raise forms.ValidationError("Title must be at least 5 characters long.")
        if len(title) > 200:
            raise forms.ValidationError("Title cannot exceed 200 characters.")
        # Pass the already-validated local value directly
        return self.check_profanity_on(title, "Your title contains inappropriate language.")

    def clean_content(self):
        # BUG FIX: same pattern — single local variable throughout
        content = self.cleaned_data.get('content', '').strip()
        if len(content) < 10:
            raise forms.ValidationError("Post content must be at least 10 characters.")
        if len(content) > 50_000:
            raise forms.ValidationError("Post content cannot exceed 50,000 characters.")
        return self.check_profanity_on(content, "Your post contains inappropriate language.")


# ---------------------------------------------------------------------------
# Contact Form
# ---------------------------------------------------------------------------

class ContactForm(forms.Form, ProfanityCleanMixin):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your name',
        }),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your email',
        })
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Subject',
        }),
    )
    message = forms.CharField(
        # BUG FIX: added max_length to prevent DoS via massive payloads
        max_length=5000,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Your message...',
        }),
    )

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError("Name is required.")
        return self.check_profanity_on(name, "Your name contains inappropriate language.")

    def clean_subject(self):
        subject = self.cleaned_data.get('subject', '').strip()
        if not subject:
            raise forms.ValidationError("Subject is required.")
        return self.check_profanity_on(subject, "Your subject contains inappropriate language.")

    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        if len(message) < 10:
            raise forms.ValidationError("Message must be at least 10 characters.")
        return self.check_profanity_on(message, "Your message contains inappropriate language.")

    def clean_email(self):
        return self.cleaned_data.get('email', '').strip().lower()


# ---------------------------------------------------------------------------
# Report Form
# ---------------------------------------------------------------------------

class ReportForm(forms.ModelForm, ProfanityCleanMixin):
    class Meta:
        model = Report
        fields = ['reason', 'description']
        widgets = {
            'reason': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Please describe the issue...',
            }),
        }

    def clean_description(self):
        desc = self.cleaned_data.get('description', '').strip()
        if len(desc) < 10:
            raise forms.ValidationError(
                "Please provide more detail (at least 10 characters)."
            )
        if len(desc) > 2000:
            raise forms.ValidationError("Description cannot exceed 2,000 characters.")
        return self.check_profanity_on(desc, "Your description contains inappropriate language.")