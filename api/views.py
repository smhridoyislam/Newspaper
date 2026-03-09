from rest_framework import viewsets, generics, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Avg
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from articles.models import Category, Article, Rating
from accounts.models import EmailVerificationToken
from .serializers import (
    UserSerializer, UserRegistrationSerializer,
    CategorySerializer, ArticleListSerializer, ArticleCategorySerializer,
    ArticleDetailSerializer, ArticleCreateUpdateSerializer,
    RatingSerializer, RatingCreateUpdateSerializer
)

User = get_user_model()


# ===================== AUTHENTICATION APIs =====================

class UserRegistrationView(generics.CreateAPIView):
    """
    User Registration API
    
    Register a new user account with email verification.
    After registration, a verification email will be sent.
    User must click the verification link to activate account.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_id='auth_register',
        operation_description="""
        ## Register a New User
        
        Creates a new user account. After successful registration:
        1. A verification email is sent to the provided email address
        2. User must click the verification link to activate account
        3. Only after activation can the user login
        
        **User Types:**
        - `viewer`: Can browse and rate articles (default)
        - `editor`: Can create, edit, and delete articles
        """,
        request_body=UserRegistrationSerializer,
        responses={
            201: openapi.Response(
                description='User registered successfully',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            400: 'Validation Error'
        },
        tags=['Authentication']
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Create verification token and send email
        token = EmailVerificationToken.objects.create(user=user)
        verification_url = request.build_absolute_uri(f'/accounts/verify-email/{token.token}/')
        
        try:
            html_message = render_to_string('accounts/email/verification_email.html', {
                'user': user,
                'verification_url': verification_url,
            })
            send_mail(
                'Verify Your Email - Newspaper Site',
                strip_tags(html_message),
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=True,
            )
        except Exception:
            pass
        
        return Response({
            'message': 'Registration successful! Please check your email to verify your account.',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    User Profile API
    
    Get or update the authenticated user's profile information.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    @swagger_auto_schema(
        operation_id='user_profile_get',
        operation_description="Get the current authenticated user's profile information.",
        responses={200: UserSerializer},
        tags=['User Profile']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_id='user_profile_update',
        operation_description="Update the current user's profile information.",
        request_body=UserSerializer,
        responses={200: UserSerializer},
        tags=['User Profile']
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_id='user_profile_partial_update',
        operation_description="Partially update the current user's profile.",
        request_body=UserSerializer,
        responses={200: UserSerializer},
        tags=['User Profile']
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


# ===================== CATEGORY APIs =====================

class CategoryViewSet(viewsets.ModelViewSet):
    """
    Category API ViewSet
    
    Manage article categories.
    
    **Available Categories:**
    - Latest
    - Politics
    - Crime
    - Opinion
    - Business
    - Sports
    - Entertainment
    - Jobs
    - Tech
    """
    queryset = Category.objects.filter(is_active=True).order_by('order')
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['order', 'name', 'created_at']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]
    
    @swagger_auto_schema(
        operation_id='categories_list',
        operation_description="""
        ## List All Categories
        
        Returns all active article categories ordered by display order.
        Each category includes the count of published articles.
        """,
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Search in name and description", type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by: order, name, created_at", type=openapi.TYPE_STRING),
        ],
        responses={200: CategorySerializer(many=True)},
        tags=['Categories']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_id='category_detail',
        operation_description="Get details of a specific category by slug.",
        responses={200: CategorySerializer, 404: 'Not Found'},
        tags=['Categories']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_id='category_create',
        operation_description="Create a new category. **Admin only.**",
        request_body=CategorySerializer,
        responses={201: CategorySerializer, 403: 'Forbidden'},
        tags=['Categories']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_id='category_update',
        operation_description="Update a category. **Admin only.**",
        request_body=CategorySerializer,
        responses={200: CategorySerializer, 403: 'Forbidden'},
        tags=['Categories']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_id='category_delete',
        operation_description="Delete a category. **Admin only.**",
        responses={204: 'No Content', 403: 'Forbidden'},
        tags=['Categories']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


# ===================== ARTICLE APIs =====================

class IsEditorOrReadOnly(permissions.BasePermission):
    """Custom permission: Editors can edit, others can only read"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and (
            request.user.is_editor() if hasattr(request.user, 'is_editor') else request.user.is_staff
        )


class ArticleViewSet(viewsets.ModelViewSet):
    """
    Article API ViewSet
    
    Full CRUD operations for news articles.
    
    **Views:**
    - **List (Homepage)**: Headline + first 50 characters of body
    - **Category Filter**: Headline + 150 characters, sorted by ratings
    - **Detail**: Full content + 2 related articles from same category
    """
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['headline', 'body']
    ordering_fields = ['publishing_time', 'views_count', 'created_at']
    
    def get_queryset(self):
        queryset = Article.objects.select_related('category', 'author')
        
        # Non-editors only see published articles
        if not self.request.user.is_authenticated or not (
            hasattr(self.request.user, 'is_editor') and self.request.user.is_editor()
        ):
            queryset = queryset.filter(status='published')
        
        # Filter by category (Category Page)
        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
            # Sort by average rating for category page
            queryset = queryset.annotate(
                avg_rating=Avg('ratings__rating')
            ).order_by('-avg_rating', '-publishing_time')
        else:
            queryset = queryset.order_by('-publishing_time')
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ArticleDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ArticleCreateUpdateSerializer
        
        # Category page: 150 chars, sorted by rating
        if self.request.query_params.get('category'):
            return ArticleCategorySerializer
        
        # Homepage: 50 chars
        return ArticleListSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'featured', 'breaking']:
            return [permissions.AllowAny()]
        return [IsEditorOrReadOnly()]
    
    def perform_create(self, serializer):
        article = serializer.save(author=self.request.user)
        if article.status == 'published':
            article.publish()
    
    @swagger_auto_schema(
        operation_id='articles_list',
        operation_description="""
        ## List Articles
        
        **Homepage View (default):**
        - Returns articles with headline and first **50 characters** of body
        - Ordered by publishing time (newest first)
        
        **Category Page View (with ?category=slug):**
        - Returns articles with headline and first **150 characters** of body
        - **Sorted by ratings** (highest rated first)
        
        ### Query Parameters:
        - `category`: Filter by category slug (e.g., `?category=politics`)
        - `search`: Search in headline and body
        - `ordering`: Sort by publishing_time, views_count, created_at
        - `page`: Page number for pagination
        """,
        manual_parameters=[
            openapi.Parameter('category', openapi.IN_QUERY, 
                description="Filter by category slug. When set, returns 150 chars and sorts by rating.", 
                type=openapi.TYPE_STRING),
            openapi.Parameter('search', openapi.IN_QUERY, 
                description="Search in headline and body", 
                type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, 
                description="Order by: publishing_time, views_count, created_at (prefix with - for descending)", 
                type=openapi.TYPE_STRING),
            openapi.Parameter('page', openapi.IN_QUERY, 
                description="Page number", 
                type=openapi.TYPE_INTEGER),
        ],
        responses={200: ArticleListSerializer(many=True)},
        tags=['Articles']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_id='article_detail',
        operation_description="""
        ## Article Detail Page
        
        Returns the full article with:
        - Complete **headline** and **full body** content
        - **2 related articles** from the same category
        - Average rating and total rating count
        - Current user's rating (if authenticated)
        - Author information
        
        **Note:** View count is incremented on each request.
        """,
        responses={200: ArticleDetailSerializer, 404: 'Not Found'},
        tags=['Articles']
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count
        instance.views_count += 1
        instance.save(update_fields=['views_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_id='article_create',
        operation_description="""
        ## Create Article (Editors Only)
        
        Create a new news article.
        
        **Required Fields:**
        - headline, body, category
        
        **Optional Fields:**
        - featured_image, image_caption, status, is_featured, is_breaking
        
        **Status Options:**
        - `draft`: Not visible to public
        - `published`: Visible to all users
        - `archived`: Hidden from listings
        """,
        request_body=ArticleCreateUpdateSerializer,
        responses={201: ArticleDetailSerializer, 403: 'Forbidden - Editors only'},
        tags=['Articles']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_id='article_update',
        operation_description="Update an article. **Editors only.**",
        request_body=ArticleCreateUpdateSerializer,
        responses={200: ArticleDetailSerializer, 403: 'Forbidden'},
        tags=['Articles']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_id='article_delete',
        operation_description="Delete an article. **Editors only.**",
        responses={204: 'No Content', 403: 'Forbidden'},
        tags=['Articles']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    @swagger_auto_schema(
        method='get',
        operation_id='articles_featured',
        operation_description="Get featured/highlighted articles (max 5).",
        responses={200: ArticleListSerializer(many=True)},
        tags=['Articles']
    )
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured articles"""
        featured = Article.objects.filter(
            is_featured=True, status='published'
        ).order_by('-publishing_time')[:5]
        serializer = ArticleListSerializer(featured, many=True, context={'request': request})
        return Response(serializer.data)
    
    @swagger_auto_schema(
        method='get',
        operation_id='articles_breaking',
        operation_description="Get breaking news articles (max 5).",
        responses={200: ArticleListSerializer(many=True)},
        tags=['Articles']
    )
    @action(detail=False, methods=['get'])
    def breaking(self, request):
        """Get breaking news"""
        breaking = Article.objects.filter(
            is_breaking=True, status='published'
        ).order_by('-publishing_time')[:5]
        serializer = ArticleListSerializer(breaking, many=True, context={'request': request})
        return Response(serializer.data)


# ===================== RATING APIs =====================

class RatingViewSet(viewsets.ModelViewSet):
    """
    Rating API ViewSet
    
    Rate articles on a scale of 0-4.
    
    **Rating Scale:**
    - 0: Poor
    - 1: Fair
    - 2: Good
    - 3: Very Good
    - 4: Excellent
    
    **Email Notification:** A confirmation email is sent after rating.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Rating.objects.filter(user=self.request.user).select_related('article', 'user')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RatingCreateUpdateSerializer
        return RatingSerializer
    
    def _send_rating_email(self, rating):
        """Send confirmation email after rating"""
        try:
            html_message = render_to_string('articles/email/rating_confirmation.html', {
                'user': rating.user,
                'article': rating.article,
                'rating': rating,
            })
            send_mail(
                f'Thank you for rating: {rating.article.headline}',
                strip_tags(html_message),
                settings.DEFAULT_FROM_EMAIL,
                [rating.user.email],
                html_message=html_message,
                fail_silently=True,
            )
        except Exception:
            pass
    
    def perform_create(self, serializer):
        rating = serializer.save()
        self._send_rating_email(rating)
    
    def perform_update(self, serializer):
        rating = serializer.save()
        self._send_rating_email(rating)
    
    @swagger_auto_schema(
        operation_id='ratings_list',
        operation_description="List all ratings submitted by the current authenticated user.",
        responses={200: RatingSerializer(many=True)},
        tags=['Ratings']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_id='rating_create',
        operation_description="""
        ## Rate an Article
        
        Submit a rating for an article (0-4 scale).
        
        **Rating Scale:**
        - **0**: Poor
        - **1**: Fair
        - **2**: Good
        - **3**: Very Good
        - **4**: Excellent
        
        **Note:** 
        - If you've already rated this article, your rating will be updated.
        - A confirmation email will be sent after rating.
        """,
        request_body=RatingCreateUpdateSerializer,
        responses={
            201: RatingSerializer,
            200: openapi.Response('Rating updated', RatingSerializer)
        },
        tags=['Ratings']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_id='rating_detail',
        operation_description="Get details of a specific rating.",
        responses={200: RatingSerializer},
        tags=['Ratings']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_id='rating_delete',
        operation_description="Delete a rating.",
        responses={204: 'No Content'},
        tags=['Ratings']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class ArticleRatingsView(generics.ListAPIView):
    """
    List all ratings for a specific article.
    """
    serializer_class = RatingSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        article_slug = self.kwargs.get('slug')
        return Rating.objects.filter(article__slug=article_slug).select_related('user', 'article')
    
    @swagger_auto_schema(
        operation_id='article_ratings_list',
        operation_description="""
        ## Get Article Ratings
        
        Returns all ratings for a specific article.
        Includes user information and comments.
        """,
        responses={200: RatingSerializer(many=True)},
        tags=['Ratings']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# ===================== DASHBOARD APIs =====================

class EditorDashboardStatsView(APIView):
    """
    Editor Dashboard Statistics API
    
    Get comprehensive statistics for the editor dashboard.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_id='dashboard_stats',
        operation_description="""
        ## Editor Dashboard Statistics
        
        Returns statistics for the authenticated editor:
        - Total articles count
        - Published articles count
        - Draft articles count
        - Archived articles count
        - Total views across all articles
        - Average rating
        - Recent articles list
        
        **Note:** Only returns data for articles created by the current user.
        """,
        responses={
            200: openapi.Response(
                description='Dashboard Statistics',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total_articles': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total number of articles'),
                        'published_articles': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of published articles'),
                        'draft_articles': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of draft articles'),
                        'archived_articles': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of archived articles'),
                        'total_views': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total views across all articles'),
                        'average_rating': openapi.Schema(type=openapi.TYPE_NUMBER, description='Average rating across all articles'),
                        'total_ratings': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total number of ratings received'),
                        'recent_articles': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    }
                )
            ),
            401: 'Unauthorized'
        },
        tags=['Dashboard']
    )
    def get(self, request):
        user = request.user
        articles = Article.objects.filter(author=user)
        
        stats = {
            'total_articles': articles.count(),
            'published_articles': articles.filter(status='published').count(),
            'draft_articles': articles.filter(status='draft').count(),
            'archived_articles': articles.filter(status='archived').count(),
            'total_views': sum(a.views_count for a in articles),
            'average_rating': round(articles.aggregate(avg=Avg('ratings__rating'))['avg'] or 0, 2),
            'total_ratings': Rating.objects.filter(article__author=user).count(),
            'recent_articles': ArticleListSerializer(
                articles.order_by('-created_at')[:5], 
                many=True, 
                context={'request': request}
            ).data
        }
        
        return Response(stats)


class HomepageDataView(APIView):
    """
    Homepage Data API
    
    Get all data needed for the homepage in a single request.
    """
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_id='homepage_data',
        operation_description="""
        ## Homepage Data
        
        Returns all data needed for homepage rendering:
        - Featured articles (up to 3)
        - Breaking news (up to 5)
        - Latest articles with headline + 50 chars body
        - All categories
        """,
        responses={
            200: openapi.Response(
                description='Homepage Data',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'featured_articles': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                        'breaking_news': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                        'latest_articles': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                        'categories': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    }
                )
            )
        },
        tags=['Pages']
    )
    def get(self, request):
        articles = Article.objects.filter(status='published').select_related('category', 'author')
        
        data = {
            'featured_articles': ArticleListSerializer(
                articles.filter(is_featured=True)[:3],
                many=True, context={'request': request}
            ).data,
            'breaking_news': ArticleListSerializer(
                articles.filter(is_breaking=True)[:5],
                many=True, context={'request': request}
            ).data,
            'latest_articles': ArticleListSerializer(
                articles.order_by('-publishing_time')[:12],
                many=True, context={'request': request}
            ).data,
            'categories': CategorySerializer(
                Category.objects.filter(is_active=True).order_by('order'),
                many=True, context={'request': request}
            ).data
        }
        
        return Response(data)
