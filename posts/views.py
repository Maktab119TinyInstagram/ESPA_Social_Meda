from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, status, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.contenttypes.models import ContentType
from social_interactions.models import Like, Comment
from django.views.generic import TemplateView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from datetime import timedelta
from rest_framework.parsers import MultiPartParser, FormParser
from django.urls import reverse_lazy
from django.db import models

from .models import Post, Media, Hashtag
from .serializers import (
    PostListSerializer, PostDetailSerializer,
    MediaSerializer, HashtagSerializer
)
from social_interactions.serializers import CommentSerializer
from accounts.models import User


class PostListCreateAPIView(generics.ListCreateAPIView):
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostListSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def perform_create(self, serializer):
        # Save post with current user
        post = serializer.save(user=self.request.user)
        
        # Process hashtags
        hashtags = self.request.data.getlist('hashtags', [])
        print(f"Hashtags from request: {hashtags}")
        
        # If the hashtags parameter is not a list, try to get it as a single value
        if not hashtags and self.request.data.get('hashtags'):
            hashtag_value = self.request.data.get('hashtags')
            if isinstance(hashtag_value, str):
                # Split by spaces or commas
                if ',' in hashtag_value:
                    hashtags = [tag.strip() for tag in hashtag_value.split(',') if tag.strip()]
                else:
                    hashtags = [tag.strip() for tag in hashtag_value.split() if tag.strip()]
                print(f"Processed hashtags from string: {hashtags}")
        
        for hashtag_title in hashtags:
            hashtag, created = Hashtag.objects.get_or_create(title=hashtag_title)
            post.hashtags.add(hashtag)
        
        # Process media files - first try with 'media_files', then with 'media'
        media_files = self.request.FILES.getlist('media_files', [])
        if not media_files:
            media_files = self.request.FILES.getlist('media', [])
            print(f"No files found with 'media_files', trying 'media': {len(media_files)} files found")
        
        # Handle case where a single file is uploaded (not as a list)
        if not media_files and 'media_files' in self.request.FILES:
            media_files = [self.request.FILES['media_files']]
            print(f"Processing single media file from 'media_files'")
        elif not media_files and 'media' in self.request.FILES:
            media_files = [self.request.FILES['media']]
            print(f"Processing single media file from 'media'")
        
        # Try to get media types and captions
        media_types = self.request.data.getlist('media_types', [])
        if not media_types and self.request.data.get('media_types'):
            media_type_value = self.request.data.get('media_types')
            if isinstance(media_type_value, str):
                media_types = [media_type_value]
                
        media_captions = self.request.data.getlist('media_captions', [])
        if not media_captions and self.request.data.get('media_captions'):
            caption_value = self.request.data.get('media_captions')
            if isinstance(caption_value, str):
                media_captions = [caption_value]
        
        # Print debug information
        print(f"Received {len(media_files)} media files")
        print(f"Received {len(media_types)} media types")
        print(f"Received {len(media_captions)} media captions")
        
        # Process each media file
        for i, media_file in enumerate(media_files):
            try:
                # Determine file type based on MIME type or extension
                if i < len(media_types) and media_types[i]:
                    file_type = media_types[i]
                else:
                    # Auto-detect file type
                    content_type = getattr(media_file, 'content_type', '')
                    if content_type and content_type.startswith('image/'):
                        file_type = 'image'
                    elif content_type and content_type.startswith('video/'):
                        file_type = 'video'
                    else:
                        # Check file extension
                        file_name = media_file.name.lower()
                        if file_name.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                            file_type = 'image'
                        elif file_name.endswith(('.mp4', '.avi', '.mov', '.wmv')):
                            file_type = 'video'
                        else:
                            file_type = 'image'  # Default to image
                
                caption = media_captions[i] if i < len(media_captions) else ''
                
                print(f"Creating Media object: file={media_file.name}, type={file_type}, caption={caption}")
                
                # Create Media object
                Media.objects.create(
                    post=post,
                    file=media_file,
                    file_type=file_type,
                    caption=caption
                )
            except Exception as e:
                print(f"Error processing media file {i}: {str(e)}")
        
        return post


class PostRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_update(self, serializer):
        post = serializer.save()
        
        # Update hashtags if provided
        if 'hashtags' in self.request.data:
            post.hashtags.clear()
            hashtags = self.request.data.getlist('hashtags', [])
            for tag_name in hashtags:
                tag, created = Hashtag.objects.get_or_create(title=tag_name.lower())
                post.hashtags.add(tag)
        
        return post


class PostLikeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        user = request.user
        
        like, created = Like.objects.get_or_create(
            user=user,
            content_type=ContentType.objects.get_for_model(Post),
            object_id=post.id
        )
        
        if not created:
            # User already liked the post, so unlike it
            like.delete()
            liked = False
        else:
            liked = True
        
        like_count = Like.objects.filter(
            content_type=ContentType.objects.get_for_model(Post),
            object_id=post.id
        ).count()
        
        return Response({
            'liked': liked,
            'count': like_count
        })


class CommentListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        return Comment.objects.filter(post_id=post_id).order_by('-created_at')
    
    def perform_create(self, serializer):
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(Post, pk=post_id)
        serializer.save(user=self.request.user, post=post)


class CommentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


class MediaCreateAPIView(generics.CreateAPIView):
    """
    API view for creating media.
    """
    serializer_class = MediaSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MediaRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting media.
    """
    queryset = Media.objects.all()
    serializer_class = MediaSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Ensure users can only access their own media.
        """
        return Media.objects.filter(post__user=self.request.user)


class HashtagListAPIView(generics.ListAPIView):
    """
    API view for listing hashtags.
    """
    queryset = Hashtag.objects.all()
    serializer_class = HashtagSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title']


class HashtagPostsAPIView(generics.ListAPIView):
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


class ExploreAPIView(generics.ListAPIView):
    """
    API view for the explore page.
    """
    serializer_class = PostListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Get the queryset of posts for the explore page.
        """
        explore_type = self.request.query_params.get('type', 'trending')
        
        if explore_type == 'latest':
            # Get latest posts
            return Post.objects.filter(is_deleted=False).order_by('-created_at')[:20]
        elif explore_type == 'photos':
            # Get posts with photos
            return Post.objects.filter(is_deleted=False, media__file_type='image').distinct().order_by('-created_at')[:20]
        elif explore_type == 'videos':
            # Get posts with videos
            return Post.objects.filter(is_deleted=False, media__file_type='video').distinct().order_by('-created_at')[:20]
        else:
            # Get trending posts (most liked and commented)
            return Post.objects.filter(is_deleted=False).annotate(
                interaction_count=Count('likes') + Count('comments')
            ).order_by('-interaction_count', '-created_at')[:20]


class SearchAPIView(generics.ListAPIView):
    """
    API view for searching posts, users, and hashtags.
    """
    serializer_class = PostListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Get the queryset of posts matching the search query.
        """
        query = self.request.query_params.get('q', '')
        
        if query:
            return Post.objects.filter(
                Q(description__icontains=query) | 
                Q(hashtags__title__icontains=query) |
                Q(user__username__icontains=query) |
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query),
                is_deleted=False
            ).distinct().select_related('user').prefetch_related('media', 'hashtags')
        
        return Post.objects.none()


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


class PostCreateView(LoginRequiredMixin, TemplateView):
    """
    View for the post creation page.
    """
    template_name = 'posts/post_create.html'
    login_url = reverse_lazy('login')


class PostDetailView(LoginRequiredMixin, DetailView):
    """
    View for the post detail page.
    """
    model = Post
    template_name = 'posts/post_detail.html'
    context_object_name = 'post'
    login_url = reverse_lazy('login')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        
        # Get comments for this post
        comments = Comment.objects.filter(post=post).order_by('-created_at')
        
        # Check if the current user has liked this post
        user_liked = Like.objects.filter(
            user=self.request.user,
            content_type=ContentType.objects.get_for_model(Post),
            object_id=post.id
        ).exists()
        
        context.update({
            'comments': comments,
            'user_liked': user_liked,
            'is_owner': post.user == self.request.user
        })
        
        return context


class PostUpdateView(generics.UpdateAPIView):
    """
    API view for updating a post.
    """
    queryset = Post.objects.filter(is_deleted=False)
    serializer_class = PostDetailSerializer
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
    login_url = reverse_lazy('login')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get trending posts (most liked in the last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        
        # Using aggregation to count likes
        post_content_type = ContentType.objects.get_for_model(Post)
        
        from django.db.models import Count, Q
        from social_interactions.models import Like
        
        # First, get post IDs that have likes within the last week
        like_counts = Like.objects.filter(
            content_type=post_content_type,
            created_at__gte=week_ago
        ).values('object_id').annotate(
            count=Count('id')
        ).order_by('-count')[:20]
        
        # Collect post IDs from the like counts
        post_ids = [item['object_id'] for item in like_counts]
        
        # Then fetch those posts preserving the order
        from django.db.models import Case, When, IntegerField
        
        if post_ids:
            # Create a Case expression to preserve the ordering
            preserved_order = Case(
                *[When(id=pk, then=pos) for pos, pk in enumerate(post_ids)],
                output_field=IntegerField()
            )
            
            # Get posts ordered by the case expression
            trending_posts = Post.objects.filter(id__in=post_ids).order_by(preserved_order)
        else:
            # Fallback if no liked posts
            trending_posts = Post.objects.none()
        
        # Get latest posts
        latest_posts = Post.objects.order_by('-created_at')[:20]
        
        # Get trending hashtags
        trending_hashtags = Hashtag.objects.annotate(
            post_count=Count('posts')
        ).order_by('-post_count')[:10]
        
        context.update({
            'trending_posts': trending_posts,
            'latest_posts': latest_posts,
            'trending_hashtags': trending_hashtags
        })
        
        return context


class HashtagPostsView(LoginRequiredMixin, TemplateView):
    """
    View for the hashtag posts page.
    """
    template_name = 'posts/hashtag_posts.html'
    login_url = reverse_lazy('login')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tag_name = self.kwargs.get('tag')
        
        hashtag = get_object_or_404(Hashtag, title=tag_name)
        posts = Post.objects.filter(hashtags=hashtag).order_by('-created_at')
        
        # Check if user follows this hashtag
        user_follows = self.request.user.following_hashtags.filter(pk=hashtag.pk).exists()
        
        context.update({
            'hashtag': hashtag,
            'posts': posts,
            'user_follows': user_follows
        })
        
        return context


class SearchView(LoginRequiredMixin, TemplateView):
    """
    View for the search page.
    """
    template_name = 'posts/search.html'
    login_url = reverse_lazy('login')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '')
        
        if query:
            # Search users
            users = User.objects.filter(
                Q(username__icontains=query) | 
                Q(first_name__icontains=query) | 
                Q(last_name__icontains=query)
            )[:10]
            
            # Search posts
            posts = Post.objects.filter(
                Q(description__icontains=query) |
                Q(location__icontains=query)
            )[:20]
            
            # Search hashtags
            hashtags = Hashtag.objects.filter(
                title__icontains=query
            )[:10]
            
            context.update({
                'query': query,
                'users': users,
                'posts': posts,
                'hashtags': hashtags,
                'has_results': users.exists() or posts.exists() or hashtags.exists()
            })
        
        return context
