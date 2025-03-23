from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django_extensions.db.models import TimeStampedModel
from phonenumber_field.modelfields import PhoneNumberField
from .manager import UserManager
from django.utils import timezone


class ROLES(models.TextChoices):
    Admin = "admin", _("Admin")
    Creator = "creator", _("Creator")
    Viewer = "viewer", _("Viewer")
    Guest = "guest", _("Guest")


cnic_regex = r"^(\d{5}-\d{7}-\d{1}|\d{5}\d{7}\d{1}|\d{5} \d{7} \d{1})$"


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    phone = PhoneNumberField(unique=True, blank=True, null=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    cnic_number = models.CharField(
        validators=[RegexValidator(cnic_regex, message="Invalid CNIC format.")],
        max_length=20,
        unique=True,
        null=True,
        blank=True,
    )
    role = models.CharField(max_length=20, choices=ROLES.choices, default=ROLES.Viewer)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["email"]

    objects = UserManager()

    def __str__(self):
        return self.username

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def is_admin(self):
        return self.is_staff

    def check_active(self):
        return self.is_active

    def has_perm(self, perm=None, obj=None):
        return self.is_staff

    def has_module_perms(self, app_label):
        return self.is_staff


class OTPService(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=255)  # Track login device
    secret_key = models.CharField(max_length=100)
    last_used = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "device_id")
        ordering = ["-created_at"]


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", blank=True, null=True
    )
    website = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"
