from rest_framework import serializers
from django.contrib.auth import get_user_model
from articles.models import Category, Article, Rating

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'user_type', 'first_name', 'last_name', 
                  'bio', 'is_premium', 'is_email_verified', 'date_joined']
        read_only_fields = ['id', 'date_joined', 'is_email_verified']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password_confirm', 'user_type']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            user_type=validated_data.get('user_type', 'viewer'),
            is_active=False  # Will be activated after email verification
        )
        return user


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    article_count = serializers.SerializerMethodField()
    url = serializers.HyperlinkedIdentityField(view_name='api:category-detail', lookup_field='slug')
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'order', 'is_active', 'article_count', 'url']
        read_only_fields = ['id']
    
    def get_article_count(self, obj):
        return obj.articles.filter(status='published').count()


class ArticleListSerializer(serializers.ModelSerializer):
    """
    Serializer for Article list view (Homepage)
    Returns headline and first 50 characters of body
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    author_name = serializers.CharField(source='author.username', read_only=True)
    average_rating = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()
    truncated_body = serializers.SerializerMethodField()
    url = serializers.HyperlinkedIdentityField(view_name='api:article-detail', lookup_field='slug')
    
    class Meta:
        model = Article
        fields = ['id', 'headline', 'slug', 'truncated_body', 'category_name', 'category_slug',
                  'author_name', 'featured_image', 'status', 'publishing_time', 'is_featured',
                  'is_breaking', 'views_count', 'average_rating', 'rating_count', 'created_at', 'url']
        read_only_fields = ['id', 'slug', 'views_count', 'created_at']
    
    def get_average_rating(self, obj):
        return obj.get_average_rating()
    
    def get_rating_count(self, obj):
        return obj.get_rating_count()
    
    def get_truncated_body(self, obj):
        """Return first 50 characters for homepage"""
        return obj.get_truncated_body(50)


class ArticleCategorySerializer(ArticleListSerializer):
    """
    Serializer for Category page view
    Returns headline and first 150 characters of body
    Articles sorted by ratings
    """
    
    def get_truncated_body(self, obj):
        """Return first 150 characters for category page"""
        return obj.get_category_truncated_body(150)


class ArticleDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for Article detail view
    Returns full headline and complete body content
    Includes 2 related articles from same category
    """
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )
    author = UserSerializer(read_only=True)
    average_rating = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()
    related_articles = serializers.SerializerMethodField()
    user_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = ['id', 'headline', 'slug', 'body', 'category', 'category_id', 'author',
                  'featured_image', 'image_caption', 'status', 'publishing_time',
                  'is_featured', 'is_breaking', 'views_count', 'average_rating',
                  'rating_count', 'user_rating', 'related_articles', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'author', 'views_count', 'created_at', 'updated_at']
    
    def get_average_rating(self, obj):
        return obj.get_average_rating()
    
    def get_rating_count(self, obj):
        return obj.get_rating_count()
    
    def get_related_articles(self, obj):
        """Get 2 related articles from same category"""
        related = obj.get_related_articles(count=2)
        return [{
            'id': article.id,
            'headline': article.headline,
            'slug': article.slug,
            'average_rating': article.get_average_rating()
        } for article in related]
    
    def get_user_rating(self, obj):
        """Get current user's rating for this article"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            rating = obj.ratings.filter(user=request.user).first()
            if rating:
                return {'rating': rating.rating, 'comment': rating.comment}
        return None


class ArticleCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating articles (Editors only)"""
    
    class Meta:
        model = Article
        fields = ['headline', 'body', 'category', 'featured_image', 'image_caption',
                  'status', 'is_featured', 'is_breaking']
    
    def validate(self, data):
        request = self.context.get('request')
        if request and hasattr(request.user, 'is_editor'):
            if not request.user.is_editor():
                raise serializers.ValidationError("Only editors can create/edit articles.")
        return data


class RatingSerializer(serializers.ModelSerializer):
    """Serializer for Rating model"""
    user = UserSerializer(read_only=True)
    article_headline = serializers.CharField(source='article.headline', read_only=True)
    article_slug = serializers.CharField(source='article.slug', read_only=True)
    
    class Meta:
        model = Rating
        fields = ['id', 'article', 'article_headline', 'article_slug', 'user', 
                  'rating', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class RatingCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating ratings
    Rating scale: 0-4
    - 0: Poor
    - 1: Fair  
    - 2: Good
    - 3: Very Good
    - 4: Excellent
    """
    
    class Meta:
        model = Rating
        fields = ['article', 'rating', 'comment']
    
    def validate_rating(self, value):
        if value < 0 or value > 4:
            raise serializers.ValidationError("Rating must be between 0 and 4.")
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user
        article = validated_data['article']
        
        # Update if already exists, otherwise create
        rating, created = Rating.objects.update_or_create(
            user=user,
            article=article,
            defaults={
                'rating': validated_data['rating'],
                'comment': validated_data.get('comment', '')
            }
        )
        return rating
