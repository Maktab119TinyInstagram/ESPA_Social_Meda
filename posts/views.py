from django.shortcuts import render
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, status, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.contenttypes.models import ContentType
from social_interactions.models import Like, Comment

from .models import Post, Media, Hashtag
from .serializers import (
    PostCreateSerializer, PostListSerializer, PostDetailSerializer,
    MediaSerializer, HashtagSerializer
)


class PostListView(generics.ListAPIView):
    """
    API view for listing posts.
    """
    serializer_class = PostListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Get the queryset of posts.
        """
        # Filter out deleted posts
        return Post.objects.filter(is_deleted=False).select_related('user').prefetch_related('media', 'hashtags')


class PostCreateView(generics.CreateAPIView):
    """
    API view for creating a post.
    """
    serializer_class = PostCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        """
        Set the user when creating a post.
        """
        serializer.save(user=self.request.user)


class PostDetailView(generics.RetrieveAPIView):
    """
    API view for retrieving a post.
    """
    queryset = Post.objects.filter(is_deleted=False)
    serializer_class = PostDetailSerializer
    permission_classes = [permissions.IsAuthenticated]


class PostUpdateView(generics.UpdateAPIView):
    """
    API view for updating a post.
    """
    queryset = Post.objects.filter(is_deleted=False)
    serializer_class = PostCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Ensure users can only update their own posts.
        """
        return Post.objects.filter(user=self.request.user, is_deleted=False)


class PostDeleteView(generics.DestroyAPIView):
    """
    API view for deleting a post.
    """
    queryset = Post.objects.filter(is_deleted=False)
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Ensure users can only delete their own posts.
        """
        return Post.objects.filter(user=self.request.user, is_deleted=False)
    
    def perform_destroy(self, instance):
        """
        Soft delete the post.
        """
        instance.is_deleted = True
        instance.save()


class UserPostsView(generics.ListAPIView):
    """
    API view for listing a user's posts.
    """
    serializer_class = PostListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Get the queryset of posts for a specific user.
        """
        user_id = self.kwargs.get('user_id')
        return Post.objects.filter(user_id=user_id, is_deleted=False).select_related('user').prefetch_related('media', 'hashtags')


class FeedView(generics.ListAPIView):
    """
    API view for the user's feed (posts from followed users).
    """
    serializer_class = PostListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Get the queryset of posts from users the current user follows.
        """
        user = self.request.user
        following_users = user.following.values_list('following_id', flat=True)
        return Post.objects.filter(user_id__in=following_users, is_deleted=False).select_related('user').prefetch_related('media', 'hashtags')


class ExploreView(generics.ListAPIView):
    """
    API view for the explore page (popular posts).
    """
    serializer_class = PostListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Get the queryset of popular posts.
        """
        # Get posts with the most likes and comments
        post_content_type = ContentType.objects.get_for_model(Post)
        
        # Count likes for each post
        posts_with_likes = Post.objects.filter(
            is_deleted=False
        ).annotate(
            likes_count=Count('like', filter=Q(like__content_type=post_content_type))
        ).annotate(
            comments_count=Count('comments')
        ).order_by('-likes_count', '-comments_count')
        
        return posts_with_likes


class HashtagListView(generics.ListAPIView):
    """
    API view for listing hashtags.
    """
    queryset = Hashtag.objects.all()
    serializer_class = HashtagSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title']


class HashtagPostsView(generics.ListAPIView):
    """
    API view for listing posts with a specific hashtag.
    """
    serializer_class = PostListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Get the queryset of posts with a specific hashtag.
        """
        hashtag_title = self.kwargs.get('title')
        return Post.objects.filter(hashtags__title=hashtag_title, is_deleted=False).select_related('user').prefetch_related('media', 'hashtags')


class SearchView(generics.ListAPIView):
    """
    API view for searching posts by description or hashtags.
    """
    serializer_class = PostListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Get the queryset of posts matching the search query.
        """
        query = self.request.query_params.get('q', '')
        if query:
            # Search in post descriptions and hashtags
            return Post.objects.filter(
                Q(description__icontains=query) | 
                Q(hashtags__title__icontains=query),
                is_deleted=False
            ).distinct().select_related('user').prefetch_related('media', 'hashtags')
        return Post.objects.none()
