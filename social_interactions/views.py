from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from .models import Comment, Like, Follow
from .serializers import CommentSerializer, LikeSerializer, FollowSerializer


class CommentCreateView(generics.CreateAPIView):
    """
    API view for creating a comment.
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        """
        Set the user when creating a comment.
        """
        serializer.save(user=self.request.user)


class CommentListView(generics.ListAPIView):
    """
    API view for listing comments for a post.
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Get the queryset of comments for a specific post.
        """
        post_id = self.kwargs.get('post_id')
        # Only get top-level comments (not replies)
        return Comment.objects.filter(post_id=post_id, parent_comment=None)


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, or deleting a comment.
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Ensure users can only update or delete their own comments.
        """
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return Comment.objects.filter(user=self.request.user)
        return Comment.objects.all()


class ReplyCreateView(generics.CreateAPIView):
    """
    API view for creating a reply to a comment.
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        """
        Set the user and parent comment when creating a reply.
        """
        parent_comment_id = self.kwargs.get('comment_id')
        parent_comment = get_object_or_404(Comment, id=parent_comment_id)
        
        # Set the post to the same as the parent comment
        serializer.save(
            user=self.request.user,
            parent_comment=parent_comment,
            post=parent_comment.post
        )


class LikeCreateView(generics.CreateAPIView):
    """
    API view for creating a like.
    """
    serializer_class = LikeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        """
        Set the user when creating a like.
        """
        serializer.save(user=self.request.user)


class LikeDeleteView(APIView):
    """
    API view for deleting a like.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, content_type_str, object_id):
        """
        Delete a like.
        """
        # Map content type string to model
        from django.contrib.contenttypes.models import ContentType
        from posts.models import Post
        
        content_type_map = {
            'post': Post,
            'comment': Comment
        }
        
        if content_type_str not in content_type_map:
            return Response(
                {'error': _('Invalid content type.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        model = content_type_map[content_type_str]
        content_type = ContentType.objects.get_for_model(model)
        
        # Delete the like
        like = Like.objects.filter(
            user=request.user,
            content_type=content_type,
            object_id=object_id
        ).first()
        
        if like:
            like.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        return Response(
            {'error': _('Like not found.')},
            status=status.HTTP_404_NOT_FOUND
        )


class FollowCreateView(generics.CreateAPIView):
    """
    API view for creating a follow relationship.
    """
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        """
        Set the follower when creating a follow relationship.
        """
        serializer.save(follower=self.request.user)


class FollowDeleteView(APIView):
    """
    API view for deleting a follow relationship.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, user_id):
        """
        Delete a follow relationship.
        """
        # Delete the follow relationship
        follow = Follow.objects.filter(
            follower=request.user,
            following_id=user_id
        ).first()
        
        if follow:
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        return Response(
            {'error': _('Follow relationship not found.')},
            status=status.HTTP_404_NOT_FOUND
        )


class FollowersListView(generics.ListAPIView):
    """
    API view for listing a user's followers.
    """
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Get the queryset of followers for a specific user.
        """
        user_id = self.kwargs.get('user_id')
        return Follow.objects.filter(following_id=user_id)


class FollowingListView(generics.ListAPIView):
    """
    API view for listing users a user is following.
    """
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Get the queryset of users a specific user is following.
        """
        user_id = self.kwargs.get('user_id')
        return Follow.objects.filter(follower_id=user_id) 