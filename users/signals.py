from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserProfile


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Create or update user profile when user is created or updated."""
    if created:
        UserProfile.objects.create(user=instance)
    else:
        # Update profile if it exists
        if hasattr(instance, "profile"):
            instance.profile.save()
