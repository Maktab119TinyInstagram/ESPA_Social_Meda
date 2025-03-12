from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    # API endpoints
    path('', views.PostListCreateAPIView.as_view(), name='post-list-create'),
    path('<int:pk>/', views.PostRetrieveUpdateDestroyAPIView.as_view(), name='post-detail'),
    path('media/', views.MediaCreateAPIView.as_view(), name='media-create'),
    path('media/<int:pk>/', views.MediaRetrieveUpdateDestroyAPIView.as_view(), name='media-detail'),
    path('hashtags/', views.HashtagListAPIView.as_view(), name='hashtag-list'),
    path('hashtags/<str:title>/', views.HashtagPostsAPIView.as_view(), name='hashtag-posts-api'),
    path('explore-api/', views.ExploreAPIView.as_view(), name='explore-api'),
    path('search/', views.SearchAPIView.as_view(), name='search-api'),
    
    # Template views
    path('explore/', views.ExploreView.as_view(), name='explore'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('create/', views.PostCreateView.as_view(), name='create'),
    path('post/<int:pk>/', views.PostDetailView.as_view(), name='post-detail'),
    path('hashtag/<str:title>/', views.HashtagPostsView.as_view(), name='hashtag-posts'),
] 