from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .views import (
    UserRegistrationView, UserProfileView,
    CategoryViewSet, ArticleViewSet, RatingViewSet,
    ArticleRatingsView, EditorDashboardStatsView, HomepageDataView
)

# ===================== SWAGGER CONFIGURATION =====================

schema_view = get_schema_view(
    openapi.Info(
        title="📰 Newspaper Site API",
        default_version='v1',
        description="""
# Newspaper Site - REST API Documentation

A comprehensive REST API for an online newspaper platform supporting article management, user authentication, and ratings.

---

## 🔐 Authentication

The API uses **Session Authentication** and **Basic Authentication**.

For authenticated endpoints, include credentials:
```
Authorization: Basic base64(email:password)
```

---

## 👥 User Types

| Type | Description | Permissions |
|------|-------------|-------------|
| **Viewer/Subscriber** | Regular users | Browse articles, rate articles |
| **Editor/Admin** | Content managers | Create, edit, delete articles |

---

## 📰 Article Views

### Homepage (Default List)
- Shows **headline** + **first 50 characters** of body
- Ordered by publishing time

### Category Page (with `?category=slug`)
- Shows **headline** + **first 150 characters** of body
- **Sorted by ratings** (highest first)

### Article Detail
- Full **headline** and **complete body**
- **2 related articles** from same category

---

## ⭐ Rating System

Rate articles on a scale of **0-4**:

| Rating | Description |
|--------|-------------|
| 0 | Poor |
| 1 | Fair |
| 2 | Good |
| 3 | Very Good |
| 4 | Excellent |

**Email notification** sent after rating submission.

---

## 📁 Categories

Available categories:
- Latest
- Politics
- Crime
- Opinion
- Business
- Sports
- Entertainment
- Jobs
- Tech

---

## 💎 Premium Features (Coming Soon)

Premium subscription placeholder is ready for future payment gateway integration.

---

## 🚀 Quick Start

1. **Register**: `POST /api/auth/register/`
2. **Verify Email**: Click link in email
3. **Login**: Use session or basic auth
4. **Browse Articles**: `GET /api/articles/`
5. **Rate Article**: `POST /api/ratings/`

        """,
        terms_of_service="https://www.newspaper-site.com/terms/",
        contact=openapi.Contact(email="admin@newspaper.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)


# ===================== ROUTER CONFIGURATION =====================

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'articles', ArticleViewSet, basename='article')
router.register(r'ratings', RatingViewSet, basename='rating')


# ===================== URL PATTERNS =====================

app_name = 'api'

urlpatterns = [
    # ===== Swagger Documentation =====
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # ===== Authentication Endpoints =====
    path('auth/register/', UserRegistrationView.as_view(), name='auth-register'),
    path('auth/profile/', UserProfileView.as_view(), name='auth-profile'),
    
    # ===== Page Data Endpoints =====
    path('pages/homepage/', HomepageDataView.as_view(), name='homepage-data'),
    
    # ===== Dashboard Endpoints =====
    path('dashboard/stats/', EditorDashboardStatsView.as_view(), name='dashboard-stats'),
    
    # ===== Article Ratings =====
    path('articles/<slug:slug>/ratings/', ArticleRatingsView.as_view(), name='article-ratings'),
    
    # ===== Router URLs (ViewSets) =====
    path('', include(router.urls)),
]
