from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Comment, Like, Follow


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    Admin for the Comment model.
    """
    list_display = ('id', 'user', 'post', 'description_preview', 'is_reply', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('description', 'user__username', 'post__description')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    def description_preview(self, obj):
        """
        Return a preview of the comment description.
        """
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_preview.short_description = _('Description')
    
    def is_reply(self, obj):
        """
        Return whether this comment is a reply to another comment.
        """
        return obj.parent_comment is not None
    is_reply.boolean = True
    is_reply.short_description = _('Is reply')


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    """
    Admin for the Like model.
    """
    list_display = ('id', 'user', 'content_type', 'object_id', 'like_type', 'created_at')
    list_filter = ('like_type', 'content_type', 'created_at')
    search_fields = ('user__username', 'object_id')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """
    Admin for the Follow model.
    """
    list_display = ('id', 'follower', 'following', 'created_at')
    search_fields = ('follower__username', 'following__username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',) 