from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class Post(models.Model):
    """
    Post model for user posts.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    description = models.TextField(_('description'), blank=True, null=True)
    location = models.CharField(_('location'), max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    is_deleted = models.BooleanField(_('deleted'), default=False)

    class Meta:
        verbose_name = _('post')
        verbose_name_plural = _('posts')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"Post by {self.user.username} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def get_media(self):
        """
        Get all media associated with this post.
        """
        return self.media.all()

    def get_hashtags(self):
        """
        Get all hashtags associated with this post.
        """
        return self.hashtags.all()

    def get_likes_count(self):
        """
        Get the number of likes for this post.
        """
        from social_interactions.models import Like
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(self)
        return Like.objects.filter(content_type=content_type, object_id=self.id).count()

    def get_comments_count(self):
        """
        Get the number of comments for this post.
        """
        return self.comments.count()


class Media(models.Model):
    """
    Media model for post images and videos.
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(_('media file'), upload_to='post_media/')
    caption = models.CharField(_('caption'), max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    # File type choices
    IMAGE = 'image'
    VIDEO = 'video'
    FILE_TYPE_CHOICES = [
        (IMAGE, _('Image')),
        (VIDEO, _('Video')),
    ]
    file_type = models.CharField(
        _('file type'),
        max_length=10,
        choices=FILE_TYPE_CHOICES,
        default=IMAGE,
    )

    class Meta:
        verbose_name = _('media')
        verbose_name_plural = _('media')
        indexes = [
            models.Index(fields=['post']),
        ]

    def __str__(self):
        return f"Media for post {self.post.id}"


class Hashtag(models.Model):
    """
    Hashtag model for post hashtags.
    """
    title = models.CharField(_('title'), max_length=50, unique=True)
    posts = models.ManyToManyField(Post, related_name='hashtags')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('hashtag')
        verbose_name_plural = _('hashtags')
        indexes = [
            models.Index(fields=['title']),
        ]

    def __str__(self):
        return f"#{self.title}"

    def get_posts_count(self):
        """
        Get the number of posts using this hashtag.
        """
        return self.posts.count()
