from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta

class User(AbstractUser):
    ROLES = (
        ('intern', 'Intern'),
        ('company', 'Company'),
    )
    role = models.CharField(max_length=20, choices=ROLES)

    email = models.EmailField(unique=True)  # ✅ Override and enforce uniqueness

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]  # Django still expects this unless you remove username fully

    def __str__(self):
        return self.email


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return timezone.now() < self.expires_at

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reset token for {self.user.email}"