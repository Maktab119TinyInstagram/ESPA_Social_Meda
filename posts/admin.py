from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Post, Media, Hashtag


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """
    Admin for the Post model.
    """
    list_display = ('id', 'user', 'description_preview', 'location', 'created_at', 'is_deleted')
    list_filter = ('is_deleted', 'created_at')
    search_fields = ('description', 'location', 'user__username', 'user__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    def description_preview(self, obj):
        """
        Return a preview of the post description.
        """
        if obj.description:
            return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
        return '-'
    description_preview.short_description = _('Description')
    
    actions = ['soft_delete_posts', 'restore_posts']
    
    def soft_delete_posts(self, request, queryset):
        """
        Soft delete selected posts.
        """
        queryset.update(is_deleted=True)
        self.message_user(request, _('Selected posts have been soft deleted.'))
    soft_delete_posts.short_description = _('Soft delete selected posts')
    
    def restore_posts(self, request, queryset):
        """
        Restore soft-deleted posts.
        """
        queryset.update(is_deleted=False)
        self.message_user(request, _('Selected posts have been restored.'))
    restore_posts.short_description = _('Restore selected posts')


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    """
    Admin for the Media model.
    """
    list_display = ('id', 'post', 'file_type', 'caption_preview', 'created_at')
    list_filter = ('file_type', 'created_at')
    search_fields = ('caption', 'post__description')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    
    def caption_preview(self, obj):
        """
        Return a preview of the media caption.
        """
        if obj.caption:
            return obj.caption[:50] + '...' if len(obj.caption) > 50 else obj.caption
        return '-'
    caption_preview.short_description = _('Caption')


@admin.register(Hashtag)
class HashtagAdmin(admin.ModelAdmin):
    """
    Admin for the Hashtag model.
    """
    list_display = ('id', 'title', 'posts_count', 'created_at')
    search_fields = ('title',)
    ordering = ('title',)
    readonly_fields = ('created_at',)
    
    def posts_count(self, obj):
        """
        Return the number of posts using this hashtag.
        """
        return obj.posts.count()
    posts_count.short_description = _('Posts count')
