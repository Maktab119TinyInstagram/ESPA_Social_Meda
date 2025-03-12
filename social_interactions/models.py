from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Comment(models.Model):
    """
    Comment model for post comments and replies.
    """
    post = models.ForeignKey('posts.Post', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    description = models.TextField(_('description'))
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('comment')
        verbose_name_plural = _('comments')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post']),
            models.Index(fields=['user']),
            models.Index(fields=['parent_comment']),
        ]

    def __str__(self):
        return f"Comment by {self.user.username} on post {self.post.id}"

    def is_reply(self):
        """
        Check if this comment is a reply to another comment.
        """
        return self.parent_comment is not None

    def get_replies(self):
        """
        Get all replies to this comment.
        """
        return self.replies.all()

    def get_likes_count(self):
        """
        Get the number of likes for this comment.
        """
        content_type = ContentType.objects.get_for_model(self)
        return Like.objects.filter(content_type=content_type, object_id=self.id).count()


class Like(models.Model):
    """
    Like model for liking posts and comments using generic relations.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes')
    
    # Generic relation to support liking different types of content
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    # Like type choices
    LIKE = 'like'
    DISLIKE = 'dislike'
    LIKE_TYPE_CHOICES = [
        (LIKE, _('Like')),
        (DISLIKE, _('Dislike')),
    ]
    like_type = models.CharField(
        _('like type'),
        max_length=10,
        choices=LIKE_TYPE_CHOICES,
        default=LIKE,
    )

    class Meta:
        verbose_name = _('like')
        verbose_name_plural = _('likes')
        # Ensure a user can only like/dislike an object once
        unique_together = ('user', 'content_type', 'object_id')
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.get_like_type_display()} by {self.user.username} on {self.content_object}"


class Follow(models.Model):
    """
    Follow model for user following relationships.
    """
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='following'
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='followers'
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('follow')
        verbose_name_plural = _('follows')
        # Ensure a user can only follow another user once
        unique_together = ('follower', 'following')
        indexes = [
            models.Index(fields=['follower']),
            models.Index(fields=['following']),
        ]

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}" 