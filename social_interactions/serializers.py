from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from .models import Comment, Like, Follow
from posts.models import Post

User = get_user_model()


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Comment model.
    """
    user = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'user', 'post', 'description', 'parent_comment',
            'created_at', 'updated_at', 'replies', 'likes_count', 'is_liked'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'replies', 'likes_count', 'is_liked']
    
    def get_user(self, obj):
        """
        Get the user who created the comment.
        """
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'profile_picture': obj.user.profile_picture.url if obj.user.profile_picture else None
        }
    
    def get_replies(self, obj):
        """
        Get the replies to this comment.
        """
        # Only get replies for top-level comments
        if obj.parent_comment is None:
            replies = obj.replies.all()
            return CommentSerializer(replies, many=True, context=self.context).data
        return []
    
    def get_likes_count(self, obj):
        """
        Get the number of likes for this comment.
        """
        return obj.get_likes_count()
    
    def get_is_liked(self, obj):
        """
        Check if the current user has liked this comment.
        """
        user = self.context.get('request').user
        if user.is_authenticated:
            content_type = ContentType.objects.get_for_model(Comment)
            return Like.objects.filter(
                user=user,
                content_type=content_type,
                object_id=obj.id,
                like_type=Like.LIKE
            ).exists()
        return False
    
    def create(self, validated_data):
        """
        Create a new comment with the validated data.
        """
        # Set the user from the request
        validated_data['user'] = self.context.get('request').user
        return super().create(validated_data)


class LikeSerializer(serializers.ModelSerializer):
    """
    Serializer for the Like model.
    """
    content_type_str = serializers.CharField(write_only=True)
    object_id = serializers.IntegerField()
    
    class Meta:
        model = Like
        fields = ['id', 'content_type_str', 'object_id', 'like_type', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate(self, attrs):
        """
        Validate the content type and object ID.
        """
        content_type_str = attrs.pop('content_type_str')
        object_id = attrs.get('object_id')
        
        # Map content type string to model
        content_type_map = {
            'post': Post,
            'comment': Comment
        }
        
        if content_type_str not in content_type_map:
            raise serializers.ValidationError(_("Invalid content type."))
        
        model = content_type_map[content_type_str]
        content_type = ContentType.objects.get_for_model(model)
        
        # Check if the object exists
        try:
            model.objects.get(id=object_id)
        except model.DoesNotExist:
            raise serializers.ValidationError(_("Object does not exist."))
        
        # Add content_type to validated data
        attrs['content_type'] = content_type
        
        return attrs
    
    def create(self, validated_data):
        """
        Create or update a like with the validated data.
        """
        user = self.context.get('request').user
        content_type = validated_data.get('content_type')
        object_id = validated_data.get('object_id')
        like_type = validated_data.get('like_type')
        
        # Check if the user has already liked/disliked this object
        like, created = Like.objects.update_or_create(
            user=user,
            content_type=content_type,
            object_id=object_id,
            defaults={'like_type': like_type}
        )
        
        return like


class FollowSerializer(serializers.ModelSerializer):
    """
    Serializer for the Follow model.
    """
    following_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Follow
        fields = ['id', 'following_id', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_following_id(self, value):
        """
        Validate that the following user exists and is not the current user.
        """
        user = self.context.get('request').user
        
        # Check if the user is trying to follow themselves
        if user.id == value:
            raise serializers.ValidationError(_("You cannot follow yourself."))
        
        # Check if the following user exists
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(_("User does not exist."))
        
        return value
    
    def create(self, validated_data):
        """
        Create a follow relationship with the validated data.
        """
        follower = self.context.get('request').user
        following_id = validated_data.get('following_id')
        following = User.objects.get(id=following_id)
        
        follow, created = Follow.objects.get_or_create(
            follower=follower,
            following=following
        )
        
        return follow 