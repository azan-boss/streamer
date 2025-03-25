import uuid
from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
import os

def video_upload_path(instance, filename):
    # Generate a unique path for each video
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('videos', 'original', filename)

def processed_video_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('videos', 'processed', filename)

def thumbnail_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('thumbnails', filename)

class Video(models.Model):
    PROCESSING_STATUS = (
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    VISIBILITY = (
        ('public', 'Public'),
        ('private', 'Private'),
        ('unlisted', 'Unlisted'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    original_file = models.FileField(
        upload_to=video_upload_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['mp4', 'mov', 'avi', 'mkv'])
        ]
    )
    
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='uploaded_videos'
    )
    
    # Metadata fields
    duration = models.FloatField(null=True, blank=True)  # in seconds
    resolution = models.CharField(max_length=20, blank=True)
    aspect_ratio = models.CharField(max_length=20, blank=True)
    framerate = models.FloatField(null=True, blank=True)
    filesize = models.BigIntegerField(null=True)  # in bytes
    
    # Processing fields
    processing_status = models.CharField(
        max_length=20, 
        choices=PROCESSING_STATUS, 
        default='queued'
    )
    processing_log = models.TextField(blank=True)
    
    # Visibility and access
    visibility = models.CharField(
        max_length=20, 
        choices=VISIBILITY, 
        default='private'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['uploader', 'visibility']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return self.title

class VideoQuality(models.Model):
    QUALITY_CHOICES = (
        ('2160p', '4K'),
        ('1440p', '2K'),
        ('1080p', 'Full HD'),
        ('720p', 'HD'),
        ('480p', 'SD'),
    )

    video = models.ForeignKey(
        Video, 
        related_name='qualities', 
        on_delete=models.CASCADE
    )
    quality = models.CharField(max_length=10, choices=QUALITY_CHOICES)
    file = models.FileField(upload_to=processed_video_path)
    bitrate = models.CharField(max_length=20)
    codec = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.video.title} - {self.get_quality_display()}"

class VideoThumbnail(models.Model):
    video = models.ForeignKey(
        Video, 
        related_name='thumbnails', 
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to=thumbnail_path)
    size = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Thumbnail for {self.video.title}"