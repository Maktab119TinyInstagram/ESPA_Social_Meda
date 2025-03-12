from django.shortcuts import render
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, status, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.contenttypes.models import ContentType
from social_interactions.models import Like, Comment
from django.views.generic import TemplateView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Post, Media, Hashtag
from .serializers import (
    PostCreateSerializer, PostListSerializer, PostDetailSerializer,
    MediaSerializer, HashtagSerializer
)
from accounts.models import User


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


class PostDetailView(LoginRequiredMixin, DetailView):
    """
    View for the post detail page.
    """
    model = Post
    template_name = 'posts/post_detail.html'
    context_object_name = 'post'
    
    def get_queryset(self):
        """
        Get the queryset of posts.
        """
        return Post.objects.filter(
            is_deleted=False
        ).select_related('user').prefetch_related('media', 'hashtags', 'comments__user')


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


class ExploreView(LoginRequiredMixin, TemplateView):
    """
    View for the explore page.
    """
    template_name = 'posts/explore.html'
    
    def get_context_data(self, **kwargs):
        """
        Add posts, users, and hashtags to the context based on the explore type.
        """
        context = super().get_context_data(**kwargs)
        
        # Get the explore type from the query parameters
        explore_type = self.request.GET.get('type', 'trending')
        
        # Get popular hashtags
        popular_hashtags = Hashtag.objects.annotate(
            post_count=Count('posts')
        ).order_by('-post_count')[:10]
        
        context['popular_hashtags'] = popular_hashtags
        
        if explore_type == 'people':
            # Get users to follow (excluding the current user and users already followed)
            following_ids = self.request.user.following.values_list('following_id', flat=True)
            users = User.objects.exclude(
                Q(id=self.request.user.id) | Q(id__in=following_ids)
            ).order_by('-date_joined')[:20]
            
            context['users'] = users
        else:
            # Get posts based on the explore type
            posts_query = Post.objects.filter(is_deleted=False).select_related('user').prefetch_related('media', 'hashtags')
            
            if explore_type == 'latest':
                # Get latest posts
                posts = posts_query.order_by('-created_at')[:20]
            elif explore_type == 'photos':
                # Get posts with photos
                posts = posts_query.filter(media__file_type='image').distinct().order_by('-created_at')[:20]
            elif explore_type == 'videos':
                # Get posts with videos
                posts = posts_query.filter(media__file_type='video').distinct().order_by('-created_at')[:20]
            else:
                # Get trending posts (most liked and commented)
                posts = posts_query.annotate(
                    interaction_count=Count('likes') + Count('comments')
                ).order_by('-interaction_count', '-created_at')[:20]
            
            context['posts'] = posts
        
        return context


class HashtagListView(generics.ListAPIView):
    """
    API view for listing hashtags.
    """
    queryset = Hashtag.objects.all()
    serializer_class = HashtagSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title']


class HashtagPostsView(LoginRequiredMixin, TemplateView):
    """
    View for the hashtag posts page.
    """
    template_name = 'posts/hashtag_posts.html'
    
    def get_context_data(self, **kwargs):
        """
        Add hashtag and posts to the context.
        """
        context = super().get_context_data(**kwargs)
        
        # Get the hashtag title from the URL
        hashtag_title = self.kwargs.get('title')
        
        # Get the hashtag
        try:
            hashtag = Hashtag.objects.get(title=hashtag_title)
            
            # Get posts with this hashtag
            posts = Post.objects.filter(
                hashtags=hashtag,
                is_deleted=False
            ).select_related('user').prefetch_related('media', 'hashtags')
            
            context['hashtag'] = hashtag
            context['posts'] = posts
        except Hashtag.DoesNotExist:
            context['hashtag'] = None
            context['posts'] = []
        
        return context


class SearchView(LoginRequiredMixin, TemplateView):
    """
    View for the search page.
    """
    template_name = 'posts/search.html'
    
    def get_context_data(self, **kwargs):
        """
        Add search results to the context.
        """
        context = super().get_context_data(**kwargs)
        
        # Get the search query from the query parameters
        query = self.request.GET.get('q', '')
        
        if query:
            # Search for posts
            posts = Post.objects.filter(
                Q(description__icontains=query) | 
                Q(hashtags__title__icontains=query) |
                Q(user__username__icontains=query) |
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query),
                is_deleted=False
            ).distinct().select_related('user').prefetch_related('media', 'hashtags')
            
            # Search for users
            users = User.objects.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            ).distinct()
            
            # Search for hashtags
            hashtags = Hashtag.objects.filter(
                title__icontains=query
            ).annotate(
                post_count=Count('posts')
            ).order_by('-post_count')
            
            context['posts'] = posts
            context['users'] = users
            context['hashtags'] = hashtags
            context['query'] = query
        
        return context


class PostCreateView(LoginRequiredMixin, TemplateView):
    """
    View for the post creation page.
    """
    template_name = 'posts/post_create.html'
