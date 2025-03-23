from django.utils.translation import gettext_lazy as _
from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
import uuid
from django_extensions.db.models import TimeStampedModel


class Video(TimeStampedModel):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    original_file = models.FileField(
        upload_to="videos/", validators=[FileExtensionValidator(["mp4", "webm", "ogg"])]
    )
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="videos"
    )
    
    # Remove duplicate duration field
    duration = models.DurationField(_("duration of the video"), null=True, blank=True)
    
    # Additional helpful fields
    upload_date = models.DateTimeField(auto_now_add=True)
    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)

    # Processing Status
    PROCESSING_STATUS = (
        ("queued", "Queued"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )
    processing_status = models.CharField(
        max_length=10, choices=PROCESSING_STATUS, default="queued"
    )
    processing_log = models.TextField(blank=True)

    # Visibility
    VISIBILITY = (
        ("public", "Public"),
        ("private", "Private"),
        ("unlisted", "Unlisted"),
    )
    visibility = models.CharField(max_length=10, choices=VISIBILITY, default="private")

    # Optimized Fields
    resolution = models.CharField(max_length=20, blank=True)
    aspect_ratio = models.CharField(max_length=20, blank=True)
    framerate = models.PositiveIntegerField(null=True, blank=True)
    filesize = models.BigIntegerField()  # In bytes

    class Meta:
        # Remove the created_at index since it's already provided by TimeStampedModel
        indexes = [
            models.Index(fields=["uploader", "visibility"]),
        ]
        ordering = ["-created"]  # Use created from TimeStampedModel

    def __str__(self):
        return self.title


class VideoQuality(models.Model):
    QUALITY_CHOICES = (
        ('2160p', '4K'),
        ('1440p', '2K'),
        ('1080p', 'HD'),
        ('720p', 'HD Ready'),
        ('480p', 'SD'),
    )
    
    video = models.ForeignKey(Video, related_name='qualities', on_delete=models.CASCADE)
    quality = models.CharField(max_length=10, choices=QUALITY_CHOICES)
    file = models.FileField(upload_to='videos/processed/')
    bitrate = models.CharField(max_length=20)
    codec = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.video.title} - {self.quality}"


class VideoThumbnail(models.Model):
    video = models.ForeignKey(Video, related_name='thumbnails', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='thumbnails/')
    size = models.CharField(max_length=20)  # e.g., '640x360'
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.video.title} - {self.size} thumbnail"
