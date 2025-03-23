from django.contrib.auth.models import BaseUserManager
from zxcvbn import zxcvbn


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        password_strength = zxcvbn(password)
        if not username:
            raise ValueError("The given username must be set")
        if not email:
            raise ValueError("The given email must be set")
        if password_strength["score"] < 3:
            suggestions = "\n".join(password_strength["feedback"]["suggestions"])
            raise ValueError(f"Password too weak. {suggestions}")

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)  # Use standard Django fields
        extra_fields.setdefault("is_superuser", True)  # Use standard Django fields
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, email, password, **extra_fields)
