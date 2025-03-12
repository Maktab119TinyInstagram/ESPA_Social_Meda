from django.urls import path

from .views import (
    PostListView, PostCreateView, PostDetailView, PostUpdateView, PostDeleteView,
    UserPostsView, FeedView, ExploreView, HashtagListView, HashtagPostsView, SearchView
)

app_name = 'posts'

urlpatterns = [
    # Posts
    path('', PostListView.as_view(), name='post-list'),
    path('create/', PostCreateView.as_view(), name='post-create'),
    path('<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('<int:pk>/update/', PostUpdateView.as_view(), name='post-update'),
    path('<int:pk>/delete/', PostDeleteView.as_view(), name='post-delete'),
    
    # User posts
    path('user/<int:user_id>/', UserPostsView.as_view(), name='user-posts'),
    
    # Feed and explore
    path('feed/', FeedView.as_view(), name='feed'),
    path('explore/', ExploreView.as_view(), name='explore'),
    
    # Hashtags
    path('hashtags/', HashtagListView.as_view(), name='hashtag-list'),
    path('hashtags/<str:title>/', HashtagPostsView.as_view(), name='hashtag-posts'),
    
    # Search
    path('search/', SearchView.as_view(), name='search'),
] 