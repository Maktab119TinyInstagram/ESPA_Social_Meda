from django.urls import path
from .views import (
    PostListCreateAPIView,
    PostRetrieveUpdateDestroyAPIView,
    PostLikeAPIView,
    CommentListCreateAPIView,
    CommentRetrieveUpdateDestroyAPIView,
    ExploreView,
    SearchView,
    PostDetailView,
    PostCreateView,
    HashtagPostsView,
    MediaCreateAPIView,
    MediaRetrieveUpdateDestroyAPIView,
    HashtagListAPIView,
    HashtagPostsAPIView,
    ExploreAPIView,
    SearchAPIView
)

app_name = 'posts'

# API Endpoints
api_urlpatterns = [
    path('', PostListCreateAPIView.as_view(), name='post-list-create'),
    path('<int:pk>/', PostRetrieveUpdateDestroyAPIView.as_view(), name='post-detail-api'),
    path('<int:pk>/like/', PostLikeAPIView.as_view(), name='post-like'),
    path('<int:post_id>/comments/', CommentListCreateAPIView.as_view(), name='comment-list-create'),
    path('comments/<int:pk>/', CommentRetrieveUpdateDestroyAPIView.as_view(), name='comment-detail'),
    path('media/', MediaCreateAPIView.as_view(), name='media-create'),
    path('media/<int:pk>/', MediaRetrieveUpdateDestroyAPIView.as_view(), name='media-detail'),
    path('hashtags/', HashtagListAPIView.as_view(), name='hashtag-list'),
    path('hashtags/<str:title>/', HashtagPostsAPIView.as_view(), name='hashtag-posts-api'),
    path('explore/', ExploreAPIView.as_view(), name='explore-api'),
    path('search/', SearchAPIView.as_view(), name='search-api'),
]

# Frontend Views
urlpatterns = [
    # Frontend views
    path('explore/', ExploreView.as_view(), name='explore'),
    path('search/', SearchView.as_view(), name='search'),
    path('post/<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('post/create/', PostCreateView.as_view(), name='post-create'),
    path('hashtag/<str:tag>/', HashtagPostsView.as_view(), name='hashtag-posts'),
]

# Add API endpoints to urlpatterns
urlpatterns += api_urlpatterns 