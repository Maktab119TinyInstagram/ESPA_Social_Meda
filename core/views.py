from django.shortcuts import render, redirect
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth import logout

from posts.models import Post


class HomeView(LoginRequiredMixin, TemplateView):
    """
    View for the home page.
    """
    template_name = 'core/home.html'
    login_url = reverse_lazy('login')
    
    def get_context_data(self, **kwargs):
        """
        Add posts from followed users to the context.
        """
        context = super().get_context_data(**kwargs)
        
        # Get the current user
        user = self.request.user
        
        # Get the IDs of users the current user follows
        following_users = user.following.values_list('following_id', flat=True)
        
        # Get posts from followed users
        posts = Post.objects.filter(
            user_id__in=following_users, 
            is_deleted=False
        ).select_related('user').prefetch_related('media', 'hashtags')
        
        context['posts'] = posts
        return context


class LoginView(TemplateView):
    """
    View for the login page.
    """
    template_name = 'accounts/login.html'


class RegisterView(TemplateView):
    """
    View for the registration page.
    """
    template_name = 'accounts/register.html'


class PasswordResetView(TemplateView):
    """
    View for the password reset page.
    """
    template_name = 'accounts/password_reset.html'


class CustomLogoutView(View):
    """
    View for logging out a user, clearing both Django session and JWT tokens.
    """
    def get(self, request):
        # Clear Django session
        logout(request)
        # Return to login page with script to clear localStorage
        return render(request, 'accounts/logout.html')
