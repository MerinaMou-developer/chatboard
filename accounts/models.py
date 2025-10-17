from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # login by email (unique), username optional
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True)
    avatar_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # no username at createsuperuser

    def __str__(self):
        return self.email
