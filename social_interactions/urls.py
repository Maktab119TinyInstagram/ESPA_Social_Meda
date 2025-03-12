from django.urls import path

from .views import (
    CommentCreateView, CommentListView, CommentDetailView, ReplyCreateView,
    LikeCreateView, LikeDeleteView, FollowCreateView, FollowDeleteView,
    FollowersListView, FollowingListView
)

app_name = 'social_interactions'

urlpatterns = [
    # Comments
    path('comments/', CommentCreateView.as_view(), name='comment-create'),
    path('posts/<int:post_id>/comments/', CommentListView.as_view(), name='comment-list'),
    path('comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),
    path('comments/<int:comment_id>/reply/', ReplyCreateView.as_view(), name='reply-create'),
    
    # Likes
    path('likes/', LikeCreateView.as_view(), name='like-create'),
    path('likes/<str:content_type_str>/<int:object_id>/', LikeDeleteView.as_view(), name='like-delete'),
    
    # Follows
    path('follows/', FollowCreateView.as_view(), name='follow-create'),
    path('follows/<int:user_id>/', FollowDeleteView.as_view(), name='follow-delete'),
    path('users/<int:user_id>/followers/', FollowersListView.as_view(), name='followers-list'),
    path('users/<int:user_id>/following/', FollowingListView.as_view(), name='following-list'),
] 