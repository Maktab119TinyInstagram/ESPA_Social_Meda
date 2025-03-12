from django.urls import path

from .views import (
    PostListCreateAPIView,
    PostRetrieveUpdateDestroyAPIView,
    PostLikeAPIView,
    CommentListCreateAPIView,
    CommentRetrieveUpdateDestroyAPIView,
    MediaCreateAPIView,
    MediaRetrieveUpdateDestroyAPIView,
    HashtagListAPIView,
    HashtagPostsAPIView,
    ExploreAPIView,
    SearchAPIView
)

app_name = 'posts_api'

urlpatterns = [
    path('', PostListCreateAPIView.as_view(), name='post-list-create'),
    path('<int:pk>/', PostRetrieveUpdateDestroyAPIView.as_view(), name='post-detail'),
    path('<int:pk>/like/', PostLikeAPIView.as_view(), name='post-like'),
    path('<int:post_id>/comments/', CommentListCreateAPIView.as_view(), name='comment-list-create'),
    path('comments/<int:pk>/', CommentRetrieveUpdateDestroyAPIView.as_view(), name='comment-detail'),
    path('media/', MediaCreateAPIView.as_view(), name='media-create'),
    path('media/<int:pk>/', MediaRetrieveUpdateDestroyAPIView.as_view(), name='media-detail'),
    path('hashtags/', HashtagListAPIView.as_view(), name='hashtag-list'),
    path('hashtags/<str:title>/', HashtagPostsAPIView.as_view(), name='hashtag-posts'),
    path('explore/', ExploreAPIView.as_view(), name='explore'),
    path('search/', SearchAPIView.as_view(), name='search'),
] 