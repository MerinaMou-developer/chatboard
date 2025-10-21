from django.urls import path
from accounts.api.base.views import RegisterView, MeView, UnreadCountsView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("me/unread-counts/", UnreadCountsView.as_view(), name="auth-unread-counts"),
]
