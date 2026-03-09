from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.db.models import Avg


class Category(models.Model):
    """Article categories"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('articles:category', kwargs={'slug': self.slug})


class Article(models.Model):
    """News Article model"""
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    )
    
    headline = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True)
    body = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='articles')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='articles')
    
    # Media
    featured_image = models.ImageField(upload_to='articles/', blank=True, null=True)
    image_caption = models.CharField(max_length=300, blank=True)
    
    # Status and timing
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    publishing_time = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    is_featured = models.BooleanField(default=False)
    is_breaking = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-publishing_time', '-created_at']
    
    def __str__(self):
        return self.headline
    
    def get_absolute_url(self):
        return reverse('articles:article_detail', kwargs={'slug': self.slug})
    
    def get_truncated_body(self, chars=50):
        """Return truncated body for homepage"""
        if len(self.body) > chars:
            return self.body[:chars] + '...'
        return self.body
    
    def get_category_truncated_body(self, chars=150):
        """Return truncated body for category page"""
        if len(self.body) > chars:
            return self.body[:chars] + '...'
        return self.body
    
    def get_average_rating(self):
        """Calculate average rating for this article"""
        avg = self.ratings.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0
    
    def get_rating_count(self):
        """Get total number of ratings"""
        return self.ratings.count()
    
    def publish(self):
        """Publish the article"""
        self.status = 'published'
        self.publishing_time = timezone.now()
        self.save()
    
    def is_published(self):
        return self.status == 'published'
    
    def get_related_articles(self, count=2):
        """Get related articles from the same category"""
        return Article.objects.filter(
            category=self.category,
            status='published'
        ).exclude(id=self.id).order_by('-publishing_time')[:count]


class Rating(models.Model):
    """User ratings for articles (0-4)"""
    
    RATING_CHOICES = (
        (0, '0 - Poor'),
        (1, '1 - Fair'),
        (2, '2 - Good'),
        (3, '3 - Very Good'),
        (4, '4 - Excellent'),
    )
    
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('article', 'user')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} rated {self.article.headline}: {self.rating}"
