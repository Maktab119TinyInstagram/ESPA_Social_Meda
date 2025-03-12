from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from .models import Post, Media, Hashtag
from social_interactions.models import Like, Comment

User = get_user_model()


class HashtagSerializer(serializers.ModelSerializer):
    """
    Serializer for the Hashtag model.
    """
    posts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Hashtag
        fields = ['id', 'title', 'posts_count', 'created_at']
        read_only_fields = ['id', 'created_at', 'posts_count']
    
    def get_posts_count(self, obj):
        """
        Get the number of posts using this hashtag.
        """
        return obj.posts.count()


class MediaSerializer(serializers.ModelSerializer):
    """
    Serializer for the Media model.
    """
    class Meta:
        model = Media
        fields = ['id', 'file', 'caption', 'file_type', 'created_at']
        read_only_fields = ['id', 'created_at']


class PostCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a Post.
    """
    media_files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )
    media_captions = serializers.ListField(
        child=serializers.CharField(max_length=255, allow_blank=True),
        write_only=True,
        required=False
    )
    media_types = serializers.ListField(
        child=serializers.ChoiceField(choices=Media.FILE_TYPE_CHOICES),
        write_only=True,
        required=False
    )
    hashtags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Post
        fields = [
            'id', 'description', 'location', 'created_at',
            'media_files', 'media_captions', 'media_types', 'hashtags'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate(self, attrs):
        """
        Validate that the media files, captions, and types have the same length.
        """
        media_files = attrs.get('media_files', [])
        media_captions = attrs.get('media_captions', [])
        media_types = attrs.get('media_types', [])
        
        if media_files and (len(media_files) != len(media_captions) or len(media_files) != len(media_types)):
            raise serializers.ValidationError(_("Media files, captions, and types must have the same length."))
        
        return attrs
    
    def create(self, validated_data):
        """
        Create a new post with the validated data.
        """
        # Extract media and hashtag data
        media_files = validated_data.pop('media_files', [])
        media_captions = validated_data.pop('media_captions', [])
        media_types = validated_data.pop('media_types', [])
        hashtag_titles = validated_data.pop('hashtags', [])
        
        # Create the post
        post = Post.objects.create(**validated_data)
        
        # Create media objects
        for i, media_file in enumerate(media_files):
            Media.objects.create(
                post=post,
                file=media_file,
                caption=media_captions[i] if i < len(media_captions) else '',
                file_type=media_types[i] if i < len(media_types) else Media.IMAGE
            )
        
        # Create or get hashtags and associate them with the post
        for title in hashtag_titles:
            # Remove # if present
            title = title.strip().lstrip('#')
            if title:
                hashtag, _ = Hashtag.objects.get_or_create(title=title.lower())
                post.hashtags.add(hashtag)
        
        return post


class PostListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing Posts.
    """
    user = serializers.SerializerMethodField()
    media = MediaSerializer(many=True, read_only=True)
    hashtags = HashtagSerializer(many=True, read_only=True)
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'user', 'description', 'location', 'created_at',
            'media', 'hashtags', 'likes_count', 'comments_count', 'is_liked'
        ]
        read_only_fields = fields
    
    def get_user(self, obj):
        """
        Get the user who created the post.
        """
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'profile_picture': obj.user.profile_picture.url if obj.user.profile_picture else None
        }
    
    def get_likes_count(self, obj):
        """
        Get the number of likes for this post.
        """
        return obj.get_likes_count()
    
    def get_comments_count(self, obj):
        """
        Get the number of comments for this post.
        """
        return obj.get_comments_count()
    
    def get_is_liked(self, obj):
        """
        Check if the current user has liked this post.
        """
        user = self.context.get('request').user
        if user.is_authenticated:
            content_type = ContentType.objects.get_for_model(Post)
            return Like.objects.filter(
                user=user,
                content_type=content_type,
                object_id=obj.id,
                like_type=Like.LIKE
            ).exists()
        return False


class PostDetailSerializer(PostListSerializer):
    """
    Serializer for detailed Post view.
    """
    comments = serializers.SerializerMethodField()
    
    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + ['comments']
    
    def get_comments(self, obj):
        """
        Get the top-level comments for this post.
        """
        from social_interactions.serializers import CommentSerializer
        
        # Get top-level comments (not replies)
        comments = obj.comments.filter(parent_comment=None)
        serializer = CommentSerializer(comments, many=True, context=self.context)
        return serializer.data 