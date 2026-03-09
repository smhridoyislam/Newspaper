from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.http import JsonResponse

from .models import Article, Category, Rating
from .forms import ArticleForm, CategoryForm, RatingForm


def home_view(request):
    """Homepage - displays articles with headline and first 50 chars of body"""
    articles = Article.objects.filter(status='published').select_related('category', 'author')
    
    # Get featured and breaking news
    featured_articles = articles.filter(is_featured=True)[:3]
    breaking_news = articles.filter(is_breaking=True)[:5]
    
    # Get latest articles for each category
    categories = Category.objects.filter(is_active=True)
    
    # Paginate all articles
    paginator = Paginator(articles, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'featured_articles': featured_articles,
        'breaking_news': breaking_news,
        'categories': categories,
    }
    return render(request, 'articles/home.html', context)


def category_view(request, slug):
    """Category page - articles sorted by ratings with first 150 chars of body"""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    
    # Get articles sorted by average rating
    articles = Article.objects.filter(
        category=category, 
        status='published'
    ).annotate(
        avg_rating=Avg('ratings__rating')
    ).order_by('-avg_rating', '-publishing_time')
    
    paginator = Paginator(articles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'articles/category.html', context)


def article_detail_view(request, slug):
    """Article detail page with full content and related articles"""
    article = get_object_or_404(Article, slug=slug, status='published')
    
    # Increment view count
    article.views_count += 1
    article.save(update_fields=['views_count'])
    
    # Get related articles from same category
    related_articles = article.get_related_articles(count=2)
    
    # Get user's existing rating if any
    user_rating = None
    if request.user.is_authenticated:
        user_rating = Rating.objects.filter(article=article, user=request.user).first()
    
    # Rating form
    rating_form = RatingForm()
    
    context = {
        'article': article,
        'related_articles': related_articles,
        'user_rating': user_rating,
        'rating_form': rating_form,
    }
    return render(request, 'articles/article_detail.html', context)


@login_required
def rate_article_view(request, slug):
    """Handle article rating and send email notification"""
    article = get_object_or_404(Article, slug=slug, status='published')
    
    if request.method == 'POST':
        # Check if user already rated
        existing_rating = Rating.objects.filter(article=article, user=request.user).first()
        
        if existing_rating:
            form = RatingForm(request.POST, instance=existing_rating)
        else:
            form = RatingForm(request.POST)
        
        if form.is_valid():
            rating = form.save(commit=False)
            rating.article = article
            rating.user = request.user
            rating.save()
            
            # Send email notification to user
            try:
                subject = f'Thank you for rating: {article.headline}'
                html_message = render_to_string('articles/email/rating_confirmation.html', {
                    'user': request.user,
                    'article': article,
                    'rating': rating,
                })
                plain_message = strip_tags(html_message)
                
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [request.user.email],
                    html_message=html_message,
                    fail_silently=True,
                )
            except Exception:
                pass  # Don't fail if email fails
            
            messages.success(request, 'Thank you for your rating!')
        else:
            messages.error(request, 'Invalid rating. Please try again.')
    
    return redirect('articles:article_detail', slug=slug)


# Editor/Admin Dashboard Views

def editor_required(view_func):
    """Decorator to check if user is an editor"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access this page.')
            return redirect('accounts:login')
        if not request.user.is_editor():
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('articles:home')
        return view_func(request, *args, **kwargs)
    return wrapper


@editor_required
def editor_dashboard_view(request):
    """Editor dashboard - overview of articles"""
    articles = Article.objects.filter(author=request.user).order_by('-created_at')
    
    # Stats
    total_articles = articles.count()
    published_articles = articles.filter(status='published').count()
    draft_articles = articles.filter(status='draft').count()
    
    # Recent articles
    recent_articles = articles[:10]
    
    context = {
        'total_articles': total_articles,
        'published_articles': published_articles,
        'draft_articles': draft_articles,
        'recent_articles': recent_articles,
    }
    return render(request, 'articles/dashboard/editor_dashboard.html', context)


@editor_required
def article_list_view(request):
    """List all articles for editor"""
    articles = Article.objects.filter(author=request.user).order_by('-created_at')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        articles = articles.filter(status=status)
    
    # Filter by category
    category_slug = request.GET.get('category')
    if category_slug:
        articles = articles.filter(category__slug=category_slug)
    
    paginator = Paginator(articles, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_status': status,
        'current_category': category_slug,
    }
    return render(request, 'articles/dashboard/article_list.html', context)


@editor_required
def article_create_view(request):
    """Create new article"""
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            
            # If publishing, set publishing time
            if article.status == 'published':
                article.publish()
            else:
                article.save()
            
            messages.success(request, 'Article created successfully!')
            return redirect('articles:article_list')
    else:
        form = ArticleForm()
    
    context = {'form': form, 'action': 'Create'}
    return render(request, 'articles/dashboard/article_form.html', context)


@editor_required
def article_edit_view(request, pk):
    """Edit existing article"""
    article = get_object_or_404(Article, pk=pk, author=request.user)
    
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            article = form.save(commit=False)
            
            # If publishing for first time, set publishing time
            if article.status == 'published' and not article.publishing_time:
                article.publish()
            else:
                article.save()
            
            messages.success(request, 'Article updated successfully!')
            return redirect('articles:article_list')
    else:
        form = ArticleForm(instance=article)
    
    context = {'form': form, 'article': article, 'action': 'Edit'}
    return render(request, 'articles/dashboard/article_form.html', context)


@editor_required
def article_delete_view(request, pk):
    """Delete article"""
    article = get_object_or_404(Article, pk=pk, author=request.user)
    
    if request.method == 'POST':
        article.delete()
        messages.success(request, 'Article deleted successfully!')
        return redirect('articles:article_list')
    
    context = {'article': article}
    return render(request, 'articles/dashboard/article_delete.html', context)


@editor_required
def category_manage_view(request):
    """Manage categories (for superusers only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Only superusers can manage categories.')
        return redirect('articles:editor_dashboard')
    
    categories = Category.objects.all().order_by('order')
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully!')
            return redirect('articles:category_manage')
    else:
        form = CategoryForm()
    
    context = {
        'categories': categories,
        'form': form,
    }
    return render(request, 'articles/dashboard/category_manage.html', context)


@editor_required
def category_edit_view(request, pk):
    """Edit category"""
    if not request.user.is_superuser:
        messages.error(request, 'Only superusers can edit categories.')
        return redirect('articles:editor_dashboard')
    
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('articles:category_manage')
    else:
        form = CategoryForm(instance=category)
    
    context = {'form': form, 'category': category}
    return render(request, 'articles/dashboard/category_edit.html', context)


@editor_required
def category_delete_view(request, pk):
    """Delete category"""
    if not request.user.is_superuser:
        messages.error(request, 'Only superusers can delete categories.')
        return redirect('articles:editor_dashboard')
    
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        if category.articles.exists():
            messages.error(request, 'Cannot delete category with existing articles.')
        else:
            category.delete()
            messages.success(request, 'Category deleted successfully!')
        return redirect('articles:category_manage')
    
    context = {'category': category}
    return render(request, 'articles/dashboard/category_delete.html', context)


def search_view(request):
    """Search articles"""
    query = request.GET.get('q', '')
    articles = []
    
    if query:
        articles = Article.objects.filter(
            status='published'
        ).filter(
            headline__icontains=query
        ) | Article.objects.filter(
            status='published'
        ).filter(
            body__icontains=query
        )
        articles = articles.distinct()
    
    paginator = Paginator(articles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'query': query,
        'page_obj': page_obj,
    }
    return render(request, 'articles/search.html', context)
