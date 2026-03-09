from django.urls import path
from . import views

app_name = 'articles'

urlpatterns = [
    # Public URLs
    path('', views.home_view, name='home'),
    path('category/<slug:slug>/', views.category_view, name='category'),
    path('article/<slug:slug>/', views.article_detail_view, name='article_detail'),
    path('article/<slug:slug>/rate/', views.rate_article_view, name='rate_article'),
    path('search/', views.search_view, name='search'),
    
    # Editor Dashboard URLs
    path('dashboard/', views.editor_dashboard_view, name='editor_dashboard'),
    path('dashboard/articles/', views.article_list_view, name='article_list'),
    path('dashboard/articles/create/', views.article_create_view, name='article_create'),
    path('dashboard/articles/<int:pk>/edit/', views.article_edit_view, name='article_edit'),
    path('dashboard/articles/<int:pk>/delete/', views.article_delete_view, name='article_delete'),
    
    # Category Management
    path('dashboard/categories/', views.category_manage_view, name='category_manage'),
    path('dashboard/categories/<int:pk>/edit/', views.category_edit_view, name='category_edit'),
    path('dashboard/categories/<int:pk>/delete/', views.category_delete_view, name='category_delete'),
]
