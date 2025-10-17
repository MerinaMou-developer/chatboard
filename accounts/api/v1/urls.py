from django.urls import path
from accounts.api.base.views import RegisterView,MeView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("me/", MeView.as_view(), name="auth-me"),
]
