from django.urls import path
from accounts.api.base.views import RegisterView, MeView, UnreadCountsView

app_name = "accounts_v1"
urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("me/unread-counts/", UnreadCountsView.as_view(), name="auth-unread-counts"),
]
