from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.db.models import Q, Count, Prefetch, OuterRef, Subquery
from .models import Category, Post, Reply, UserProfile, Notification, PostView
from django.utils import timezone
from .forms import CustomUserCreationForm, ProfileForm, EmailAuthenticationForm, PostForm, ContactForm, ReportForm
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.contrib.auth.models import User
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.cache import cache_page
from django.db.models import F
from .forms import check_profanity
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.http import JsonResponse
from django.contrib.auth.tokens import default_token_generator
from django.db.models.functions import Coalesce
from django.db.models import IntegerField



# ==================== AUTHENTICATION ====================
import resend


def _reply_count_subquery():
    """
    Postgres-safe reply count.

    Using .annotate(reply_count=Count('replies')) together with
    select_related() across a joined table (e.g. author__userprofile)
    makes Django build a GROUP BY that can omit columns pulled in via
    the join, which Postgres rejects (SQLite silently allows it, which
    is why this only ever broke in production). A correlated subquery
    sidesteps the join/GROUP BY entirely.
    """
    return Coalesce(
        Subquery(
            Reply.objects.filter(post=OuterRef('pk'))
            .order_by()
            .values('post')
            .annotate(c=Count('id'))
            .values('c'),
        ),
        0,
        output_field=IntegerField(),
    )

SITE_URL = 'https://www.womenkonnect.co.in'


def _iso(dt):
    """ISO-8601 datetime, or None if the value is missing/invalid."""
    if not dt:
        return None
    try:
        return dt.isoformat()
    except Exception:
        return None


def _post_forum_posting(post):
    """
    Build one DiscussionForumPosting dict for a post. Returns None if the
    post doesn't have a valid created_at — better to omit that single item
    than to emit a broken/null datePublished for it.

    Building this as a plain Python dict and letting json.dumps() serialize
    it (rather than hand-writing JSON inside the template with the
    `escapejs` filter) is what actually makes this safe for post titles
    containing emoji or other special Unicode — escapejs has known gaps
    with characters outside the BMP (many emoji), which was corrupting the
    JSON for any post title containing them, and knocking out neighboring
    items in the same list along with it.
    """
    date_published = _iso(post.created_at)
    if not date_published:
        return None
    return {
        "@type": "DiscussionForumPosting",
        "headline": post.title,
        "url": f"{SITE_URL}{reverse('post_detail', args=[post.pk])}",
        "datePublished": date_published,
        "dateModified": _iso(post.updated_at) or date_published,
        "author": {
            "@type": "Person",
            "name": post.author.username,
            "url": f"{SITE_URL}/",
        },
        "interactionStatistic": [
            {
                "@type": "InteractionCounter",
                "interactionType": "https://schema.org/LikeAction",
                "userInteractionCount": post.total_likes(),
            },
            {
                "@type": "InteractionCounter",
                "interactionType": "https://schema.org/CommentAction",
                "userInteractionCount": getattr(post, 'reply_count', 0),
            },
        ],
    }


def _category_structured_data(category, posts):
    return {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": f"{category.name} – WomenKonnect",
        "description": category.description,
        "url": f"{SITE_URL}/category/{category.slug}/",
        "isPartOf": {
            "@type": "WebSite",
            "name": "WomenKonnect",
            "url": SITE_URL,
        },
        "hasPart": [item for item in (_post_forum_posting(p) for p in posts) if item],
    }


def _reply_comment(reply):
    """One schema.org Comment object for a single reply."""
    date_published = _iso(reply.created_at)
    comment = {
        "@type": "Comment",
        "text": reply.content[:400],
        "author": {
            "@type": "Person",
            "name": reply.author.username,
            "url": f"{SITE_URL}/",
        },
        "url": f"{SITE_URL}{reverse('post_detail', args=[reply.post_id])}#reply-{reply.pk}",
    }
    if date_published:
        comment["datePublished"] = date_published
    return comment


def _post_structured_data(post, replies_qs):
    """
    replies_qs: the full (unpaginated) queryset of replies for this post,
    already select_related for author/author__userprofile.
    """
    replies_list = list(replies_qs)
    comment_count = len(replies_list)

    data = _post_forum_posting(post)
    if data is None:
        # Shouldn't normally happen (post already exists and was just
        # fetched), but fall back to a minimal valid block rather than
        # emitting nothing.
        data = {
            "@type": "DiscussionForumPosting",
            "headline": post.title,
            "url": f"{SITE_URL}{reverse('post_detail', args=[post.pk])}",
        }
    data["@context"] = "https://schema.org"
    data["text"] = post.content[:400]
    # Use the actual comment count (all replies, not just the current
    # pagination page).
    for stat in data.get("interactionStatistic", []):
        if stat.get("interactionType") == "https://schema.org/CommentAction":
            stat["userInteractionCount"] = comment_count
    data["isPartOf"] = {
        "@type": "WebSite",
        "name": "WomenKonnect",
        "url": SITE_URL,
    }
    # Google's Discussion Forum feature wants actual comment content, not
    # just a count — cap at 50 to keep the payload reasonable on posts
    # with very long reply threads.
    data["comment"] = [_reply_comment(r) for r in replies_list[:50]]
    return data


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.save()

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = account_activation_token.make_token(user)
            activation_link = f"{settings.SITE_URL}/activate/{uid}/{token}/"

            try:
                resend.api_key = settings.RESEND_API_KEY
                resend.Emails.send({
                    "from": settings.DEFAULT_FROM_EMAIL,
                    "to": [user.email],
                    "subject": "Activate your WomenKonnect account",
                    "text": f"Hi {user.username},\n\nClick the link to activate:\n{activation_link}",
                })
                messages.success(request, "✅ Account created! Check your email to activate.")
            except Exception as e:
                    
                print(f"RESEND ERROR: {type(e).__name__}: {str(e)}")
                user.delete()
                messages.error(request, f"Registration failed: {str(e)}")
                return render(request, "community/register.html", {"form": form})
                
            return redirect('login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()

    return render(request, "community/register.html", {"form": form})
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        form = EmailAuthenticationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                user_obj = User.objects.get(email__iexact=email)
                user = authenticate(request, username=email, password=password)
            except User.DoesNotExist:
                user = None

            if user is not None:
                if user.is_active:
                    login(request, user)
                    next_url = request.GET.get('next', '')
                    # Prevent open redirect: only allow relative URLs
                    if next_url and next_url.startswith('/') and not next_url.startswith('//'):
                        return redirect(next_url)
                    return redirect('home')
                else:
                    messages.error(request, "Account not activated. Please check your email for the activation link.")
            else:
                messages.error(request, "Invalid email or password.")
    else:
        form = EmailAuthenticationForm()

    return render(request, 'community/login.html', {'form': form})


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Your account has been activated successfully! You can now login.')
        return redirect('login')
    else:
        messages.error(request, 'Activation link is invalid or has expired!')
        return redirect('register')


# ==================== HOME & CATEGORIES ====================

def home(request):
    categories = Category.objects.all()

    cutoff = timezone.now() - timezone.timedelta(hours=48)

    # Single chronological feed (newest first). Posts within the last 48
    # hours are flagged so the template can show a "New" badge — no more
    # splitting into separate Recent/Older columns.
    posts = Post.objects.select_related('author', 'category', 'author__userprofile')\
        .prefetch_related('likes')\
        .annotate(reply_count=_reply_count_subquery())\
        .order_by('-created_at')[:30]

    context = {
        'categories': categories,
        'posts': posts,
        'cutoff': cutoff,
        'total_members': User.objects.count(),
        'total_posts': Post.objects.count(),
    }

    return render(request, 'community/home_two_panel.html', context)


def category_posts(request, slug):
    category = get_object_or_404(Category, slug=slug)

    # Optimized query
    posts = Post.objects.filter(category=category)\
        .select_related('author', 'author__userprofile')\
        .prefetch_related('likes')\
        .annotate(reply_count=_reply_count_subquery())\
        .order_by('-is_pinned', '-created_at')

    context = {
        'category': category,
        'posts': posts,
        'structured_data': json.dumps(_category_structured_data(category, posts), ensure_ascii=False),
    }
    return render(request, 'community/category_posts.html', context)


# ==================== POST VIEWS ====================

def post_detail(request, pk):
    # Optimized query
    post = get_object_or_404(
        Post.objects.select_related('author', 'author__userprofile', 'category'),
        pk=pk
    )

    # Count each visitor (logged in or not) at most once per browser
    # session, so refreshing the page doesn't inflate view_count.
    session_key = f'viewed_post_{post.pk}'
    if not request.session.get(session_key, False):
        post.increment_views()
        request.session[session_key] = True

    # For logged-in readers, record that they've seen this post so the
    # author can later see who's engaged with it. Anonymous readers still
    # count toward view_count above but aren't identifiable, so nothing
    # to record here for them.
    if request.user.is_authenticated:
        PostView.objects.get_or_create(post=post, user=request.user)

    # Get all replies with optimized query
    replies_list = post.replies.select_related('author', 'author__userprofile', 'quoted_user')\
        .prefetch_related('likes')\
        .order_by('created_at')

    # Pagination - 10 replies per page
    paginator = Paginator(replies_list, 10)
    page = request.GET.get('page', 1)

    try:
        replies = paginator.page(page)
    except PageNotAnInteger:
        replies = paginator.page(1)
    except EmptyPage:
        replies = paginator.page(paginator.num_pages)

    context = {
        'post': post,
        'replies': replies,
        'structured_data': json.dumps(
            _post_structured_data(post, replies_list),
            ensure_ascii=False,
        ),
    }

    # "Seen by" list — only ever shown to the post's own author, to
    # respect readers' privacy on a site whose whole promise is being a
    # safe, anonymous space.
    if request.user.is_authenticated and request.user == post.author:
        context['viewers'] = post.post_views.select_related('user', 'user__userprofile')[:50]

    return render(request, 'community/post_detail.html', context)


@login_required
def create_post(request, category_slug=None):
    preselected_category = None
    if category_slug:
        preselected_category = get_object_or_404(Category, slug=category_slug)

    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Post created successfully!')
            return redirect('post_detail', pk=post.pk)
    else:
        initial = {}
        if preselected_category:
            initial['category'] = preselected_category
        form = PostForm(initial=initial)

    return render(request, "community/create_post.html", {
        "form": form,
        "preselected_category": preselected_category,
    })


@login_required
def edit_post(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if post.author != request.user:
        messages.error(request, 'You can only edit your own posts!')
        return redirect('post_detail', pk=pk)

    if not post.can_edit():
        messages.error(request, 'You can only edit posts within 24 hours of creation!')
        return redirect('post_detail', pk=pk)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Post updated successfully!')
            return redirect('post_detail', pk=pk)
    else:
        form = PostForm(instance=post)

    return render(request, 'community/edit_post.html', {'form': form, 'post': post})


@login_required
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if post.author != request.user and not request.user.is_staff:
        messages.error(request, 'You can only delete your own posts!')
        return redirect('post_detail', pk=pk)

    if not post.can_edit() and not request.user.is_staff:
        messages.error(request, 'You can only delete posts within 24 hours of creation!')
        return redirect('post_detail', pk=pk)

    if request.method == 'POST':
        category_slug = post.category.slug
        post.delete()
        messages.success(request, 'Post deleted successfully!')
        return redirect('category_posts', slug=category_slug)

    return render(request, 'community/delete_post.html', {'post': post})


# ==================== REPLY VIEWS ====================

@login_required
def add_reply(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if post.is_locked:
        messages.error(request, 'This post is locked and no longer accepts replies.')
        return redirect('post_detail', pk=pk)

    if request.method == 'POST':
        content = request.POST.get('content')
        quoted_user_id = request.POST.get('quoted_user_id')
        quoted_user = None

        if quoted_user_id:
            try:
                quoted_user = User.objects.get(id=quoted_user_id)
            except User.DoesNotExist:
                quoted_user = None

        if not content or not content.strip():
            messages.error(request, 'Reply content cannot be empty.')
            return redirect('post_detail', pk=pk)

        if check_profanity(content):
            messages.error(request, 'Your reply contains inappropriate language. Please revise it.')
            return redirect('post_detail', pk=pk)

        reply = Reply.objects.create(
            post=post,
            author=request.user,
            content=content.strip(),
            quoted_user=quoted_user
        )

        # Create notification for post author
        if post.author != request.user:
            Notification.objects.create(
                user=post.author,
                notification_type='reply',
                message=f"{request.user.username} replied to your post",
                post=post,
                reply=reply,
                from_user=request.user
            )

        messages.success(request, 'Reply added successfully!')
        return redirect('post_detail', pk=pk)

    return redirect('post_detail', pk=pk)


@login_required
def edit_reply(request, pk):
    reply = get_object_or_404(Reply, pk=pk)

    if reply.author != request.user:
        messages.error(request, 'You can only edit your own replies!')
        return redirect('post_detail', pk=reply.post.pk)

    if not reply.can_edit():
        messages.error(request, 'You can only edit replies within 24 hours!')
        return redirect('post_detail', pk=reply.post.pk)

    if request.method == 'POST':
        new_content = request.POST.get('content', '').strip()
        if not new_content:
            messages.error(request, 'Reply content cannot be empty.')
            return redirect('edit_reply', pk=pk)
        if check_profanity(new_content):
            messages.error(request, 'Your reply contains inappropriate language. Please revise it.')
            return redirect('edit_reply', pk=pk)
        reply.content = new_content
        reply.save()
        messages.success(request, 'Reply updated successfully!')
        return redirect('post_detail', pk=reply.post.pk)

    return render(request, 'community/edit_reply.html', {'reply': reply})


@login_required
def delete_reply(request, pk):
    reply = get_object_or_404(Reply, pk=pk)

    if reply.author != request.user and not request.user.is_staff:
        messages.error(request, 'You can only delete your own replies!')
        return redirect('post_detail', pk=reply.post.pk)

    if not reply.can_edit() and not request.user.is_staff:
        messages.error(request, 'You can only delete replies within 24 hours!')
        return redirect('post_detail', pk=reply.post.pk)

    post_pk = reply.post.pk
    if request.method == 'POST':
        reply.delete()
        messages.success(request, 'Reply deleted successfully!')
        return redirect('post_detail', pk=post_pk)

    return render(request, 'community/delete_reply.html', {'reply': reply})


# ==================== LIKE FUNCTIONALITY ====================

@login_required
@require_POST
def like_post(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True

        # Create notification for post author (only once per user per post)
        if post.author != request.user:
            Notification.objects.get_or_create(
                user=post.author,
                notification_type='like',
                post=post,
                from_user=request.user,
                defaults={'message': f"{request.user.username} liked your post"}
            )

    # Return JSON for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'total_likes': post.total_likes()
        })

    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
@require_POST
def like_reply(request, pk):
    reply = get_object_or_404(Reply, pk=pk)

    if request.user in reply.likes.all():
        reply.likes.remove(request.user)
        liked = False
    else:
        reply.likes.add(request.user)
        liked = True

        # Create notification for reply author (only once per user per reply)
        if reply.author != request.user:
            Notification.objects.get_or_create(
                user=reply.author,
                notification_type='like',
                reply=reply,
                from_user=request.user,
                defaults={
                    'message': f"{request.user.username} liked your reply",
                    'post': reply.post,
                }
            )

    # Return JSON for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'total_likes': reply.total_likes()
        })

    return redirect(request.META.get('HTTP_REFERER', 'home'))


# ==================== PROFILE ====================

@login_required
def profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    user_posts = Post.objects.filter(author=request.user)\
        .select_related('category')\
        .annotate(reply_count=_reply_count_subquery())\
        .order_by('-created_at')

    context = {
        'profile': profile,
        'user_posts': user_posts,
    }
    return render(request, 'community/profile.html', context)


@login_required
def edit_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'community/edit_profile.html', {'form': form})


# ==================== SEARCH ====================

def search(request):
    query = request.GET.get('q', '').strip()
    posts = []

    if len(query) >= 2:
        posts = Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        ).select_related('author', 'category', 'author__userprofile')\
         .prefetch_related('likes')\
         .annotate(reply_count=_reply_count_subquery())[:20]
    elif query:
        query = ''  # too short — template will show hint

    context = {
        'posts': posts,
        'query': query,
    }
    return render(request, 'community/search_results.html', context)


# ==================== NOTIFICATIONS ====================

@login_required
def notifications(request):
    user_notifications = Notification.objects.filter(user=request.user)\
        .select_related('from_user', 'post', 'reply')[:20]

    # Mark all as read
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)

    context = {
        'notifications': user_notifications,
    }
    return render(request, 'community/notifications.html', context)


@login_required
def unread_notifications_count(request):
    """API endpoint for unread notification count"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})



# ==================== PIN POST ====================

@login_required
@require_POST
def pin_post(request, pk):
    """Only staff/superusers can pin posts"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to pin posts.')
        return redirect('post_detail', pk=pk)

    post = get_object_or_404(Post, pk=pk)
    post.is_pinned = not post.is_pinned
    post.save(update_fields=['is_pinned'])
    action = 'pinned' if post.is_pinned else 'unpinned'
    messages.success(request, f'Post {action} successfully.')
    return redirect('post_detail', pk=pk)

@login_required
def report_post(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.post = post
            report.save()
            messages.success(request, "Post reported successfully. Our team will review it.")
            return redirect('post_detail', pk=pk)
    else:
        form = ReportForm()

    return render(request, 'community/report.html', {'form': form, 'target': post, 'target_type': 'post'})


@login_required
def report_reply(request, pk):
    reply = get_object_or_404(Reply, pk=pk)

    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.reply = reply
            report.post = reply.post
            report.save()
            messages.success(request, "Reply reported successfully. Our team will review it.")
            return redirect('post_detail', pk=reply.post.pk)
    else:
        form = ReportForm()

    return render(request, 'community/report.html', {'form': form, 'target': reply, 'target_type': 'reply'})


# ==================== STATIC PAGES ====================

def about(request):
    return render(request, "community/about.html")


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            try:
                resend.api_key = settings.RESEND_API_KEY
                resend.Emails.send({
                    "from": settings.DEFAULT_FROM_EMAIL,
                    "to": [settings.ADMIN_EMAIL],
                    "reply_to": form.cleaned_data['email'],   # ← add this
                    "subject": f"Contact: {form.cleaned_data['subject']}",
                    "text": f"From: {form.cleaned_data['name']} <{form.cleaned_data['email']}>\n\n{form.cleaned_data['message']}",
                })
                messages.success(request, "Your message has been sent! We'll get back to you soon.")
            except Exception as e:
                print(f"Contact email error: {e}")
                messages.error(request, "Sorry, couldn't send your message. Please try again.")
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, "community/contact.html", {"form": form})
# Error handlers
def handler404(request, exception):
    return render(request, '404.html', status=404)

def handler500(request):
    return render(request, '500.html', status=500)

def handler403(request, exception):
    return render(request, '403.html', status=403)

def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get('email', '').strip().lower()
        try:
            user = User.objects.get(email__iexact=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"{settings.SITE_URL}/password-reset-confirm/{uid}/{token}/"

            resend.api_key = settings.RESEND_API_KEY
            resend.Emails.send({
                "from": settings.DEFAULT_FROM_EMAIL,
                "to": [user.email],
                "subject": "Reset your WomenKonnect password",
                "text": f"Hi {user.username},\n\nClick the link to reset your password:\n{reset_link}\n\nIf you didn't request this, ignore this email.",
            })
        except User.DoesNotExist:
            pass

        messages.success(request, "If that email exists, a reset link has been sent.")
        return redirect('forgot_password')

    return render(request, "community/password_reset.html")


def reset_password_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is None or not default_token_generator.check_token(user, token):
        messages.error(request, 'Reset link is invalid or has expired!')
        return redirect('forgot_password')

    if request.method == "POST":
        password1 = request.POST.get('new_password1')
        password2 = request.POST.get('new_password2')
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'community/password_reset_confirm.html', {'uidb64': uidb64, 'token': token, 'validlink': True})

        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return render(request, 'community/password_reset_confirm.html', {'uidb64': uidb64, 'token': token, 'validlink': True})

        user.set_password(password1)
        user.save()
        messages.success(request, 'Password reset successfully! You can now login.')
        return redirect('login')

    return render(request, 'community/password_reset_confirm.html', {'uidb64': uidb64, 'token': token, 'validlink': True})
def privacy_policy(request):
    return render(request, "community/privacy_policy.html")