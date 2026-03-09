from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid


class CustomUser(AbstractUser):
    """Custom User model supporting both editors and viewers"""
    
    USER_TYPE_CHOICES = (
        ('viewer', 'Viewer/Subscriber'),
        ('editor', 'Editor/Admin'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='viewer')
    email = models.EmailField(unique=True)
    is_email_verified = models.BooleanField(default=False)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    
    # Premium subscription placeholder
    is_premium = models.BooleanField(default=False)
    premium_expiry = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email
    
    def is_editor(self):
        return self.user_type == 'editor' or self.is_staff
    
    def is_viewer(self):
        return self.user_type == 'viewer'
    
    def has_premium_access(self):
        """Check if user has active premium subscription"""
        if not self.is_premium:
            return False
        if self.premium_expiry and self.premium_expiry < timezone.now():
            return False
        return True


class EmailVerificationToken(models.Model):
    """Token for email verification"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='verification_tokens')
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Token for {self.user.email}"
    
    def is_valid(self):
        """Check if token is still valid (24 hours)"""
        from datetime import timedelta
        return (
            not self.is_used and 
            timezone.now() < self.created_at + timedelta(hours=24)
        )
