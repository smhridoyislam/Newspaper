from django.contrib import admin
from .models import Category, Article, Rating


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['headline', 'category', 'author', 'status', 'publishing_time', 'views_count', 'get_average_rating']
    list_filter = ['status', 'category', 'is_featured', 'is_breaking', 'created_at']
    search_fields = ['headline', 'body', 'author__username']
    prepopulated_fields = {'slug': ('headline',)}
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    raw_id_fields = ['author']
    
    fieldsets = (
        ('Content', {
            'fields': ('headline', 'slug', 'body', 'category')
        }),
        ('Media', {
            'fields': ('featured_image', 'image_caption')
        }),
        ('Status', {
            'fields': ('status', 'publishing_time', 'is_featured', 'is_breaking')
        }),
        ('Author', {
            'fields': ('author',)
        }),
    )
    
    def get_average_rating(self, obj):
        return obj.get_average_rating()
    get_average_rating.short_description = 'Avg Rating'


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['article', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['article__headline', 'user__email']
    raw_id_fields = ['article', 'user']
    ordering = ['-created_at']
