from rest_framework import serializers
from django.core.files.uploadedfile import TemporaryUploadedFile
import ffmpeg
import os

from .models import Video, VideoQuality, VideoThumbnail

class VideoThumbnailSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoThumbnail
        fields = ['image', 'size', 'is_default']

class VideoQualitySerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoQuality
        fields = ['quality', 'file', 'bitrate', 'codec']

class VideoSerializer(serializers.ModelSerializer):
    qualities = VideoQualitySerializer(many=True, read_only=True)
    thumbnails = VideoThumbnailSerializer(many=True, read_only=True)
    
    class Meta:
        model = Video
        fields = [
            'id', 'title', 'description', 'original_file', 
            'uploader', 'duration', 'resolution', 
            'aspect_ratio', 'framerate', 'filesize',
            'processing_status', 'visibility',
            'qualities', 'thumbnails',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'uploader', 'duration', 'resolution', 
            'aspect_ratio', 'framerate', 'filesize',
            'processing_status', 'qualities', 'thumbnails',
            'created_at', 'updated_at'
        ]
    
    def validate_original_file(self, value):
        """
        Validate video file before upload
        
        Checks:
        - File size (max 5GB)
        - Video stream presence
        - Video codec compatibility
        """
        # Validate file size (max 5GB)
        max_size = 5 * 1024 * 1024 * 1024  # 5 GB
        if value.size > max_size:
            raise serializers.ValidationError("File too large. Max size is 5GB.")
        
        # Temporary file for validation
        if isinstance(value, TemporaryUploadedFile):
            temp_path = value.temporary_file_path()
        else:
            raise serializers.ValidationError("Invalid file upload.")
        
        try:
            # Use ffprobe to validate video
            probe = ffmpeg.probe(temp_path)
            video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
            
            if not video_stream:
                raise serializers.ValidationError("No video stream found in the file.")
            
            # Optional: Add more specific codec or resolution checks
            width = int(video_stream.get('width', 0))
            height = int(video_stream.get('height', 0))
            
            if width == 0 or height == 0:
                raise serializers.ValidationError("Invalid video resolution.")
            
        except ffmpeg.Error as e:
            raise serializers.ValidationError(f"Video validation failed: {str(e)}")
        
        return value
    
    def create(self, validated_data):
        """
        Custom create method to set uploader and start processing
        """
        # Set uploader from request context
        validated_data['uploader'] = self.context['request'].user
        
        # Create video object
        video = super().create(validated_data)
        
        # Trigger async processing
        from .tasks import process_video
        process_video.delay(str(video.id))
        
        return video