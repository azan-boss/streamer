# videos/tasks.py
import os
import uuid
import logging
from django.conf import settings
from django.core.files import File

import ffmpeg
from celery import shared_task
from .models import Video, VideoQuality, VideoThumbnail

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_video(self, video_id):
    """
    Comprehensive video processing task with robust error handling
    
    1. Extract video metadata
    2. Generate thumbnails
    3. Transcode to multiple qualities
    4. Handle errors gracefully
    """
    try:
        # Retrieve video object
        video = Video.objects.get(id=video_id)
        
        # Update processing status
        video.processing_status = 'processing'
        video.save()
        
        # Ensure input file exists
        input_path = video.original_file.path
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Video file not found: {input_path}")
        
        # Create output directories
        output_base_dir = os.path.join(settings.MEDIA_ROOT, 'videos', str(video.id))
        os.makedirs(output_base_dir, exist_ok=True)
        
        # Extract video metadata using ffprobe
        probe = ffmpeg.probe(input_path)
        video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
        
        if not video_stream:
            raise ValueError("No video stream found in the file")
        
        # Update video metadata
        video.duration = float(video_stream.get('duration', 0))
        video.resolution = f"{video_stream.get('width', 0)}x{video_stream.get('height', 0)}"
        video.aspect_ratio = video_stream.get('display_aspect_ratio', '')
        video.framerate = float(eval(video_stream.get('r_frame_rate', '0/1')))
        video.save()
        
        # Generate thumbnails
        generate_thumbnails(video, input_path, output_base_dir)
        
        # Transcode video to multiple qualities
        qualities = [
            {'name': '2160p', 'vf': 'scale=-2:2160', 'bitrate': '8000k'},
            {'name': '1080p', 'vf': 'scale=-2:1080', 'bitrate': '5000k'},
            {'name': '720p', 'vf': 'scale=-2:720', 'bitrate': '2500k'},
        ]
        
        for quality in qualities:
            output_filename = f"{video.id}_{quality['name']}.mp4"
            output_path = os.path.join(output_base_dir, output_filename)
            
            try:
                (
                    ffmpeg
                    .input(input_path)
                    .filter('scale', quality['vf'])
                    .output(
                        output_path, 
                        vcodec='libx264', 
                        acodec='aac', 
                        **{
                            'b:v': quality['bitrate'],
                            'b:a': '192k',
                            'preset': 'medium'
                        }
                    )
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
                
                # Create VideoQuality object
                with open(output_path, 'rb') as f:
                    quality_file = File(f, name=output_filename)
                    VideoQuality.objects.create(
                        video=video,
                        quality=quality['name'],
                        file=quality_file,
                        bitrate=quality['bitrate'],
                        codec='h264'
                    )
            
            except ffmpeg.Error as e:
                logger.error(f"Transcoding error for {quality['name']}: {e.stderr.decode()}")
                continue
        
        # Mark video as processed
        video.processing_status = 'completed'
        video.save()
        
        return str(video.id)
    
    except Exception as e:
        # Log the full error and update video status
        logger.error(f"Video processing failed: {str(e)}", exc_info=True)
        
        video.processing_status = 'failed'
        video.processing_log = str(e)
        video.save()
        
        # Retry the task with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)

def generate_thumbnails(video, input_path, output_base_dir):
    """
    Generate multiple thumbnails for a video
    
    Args:
        video (Video): Video model instance
        input_path (str): Path to the original video file
        output_base_dir (str): Base directory to save thumbnails
    """
    # Create thumbnails directory
    thumbnails_dir = os.path.join(output_base_dir, 'thumbnails')
    os.makedirs(thumbnails_dir, exist_ok=True)
    
    # Define thumbnail timestamps and sizes
    thumbnail_configs = [
        {'timestamp': 5, 'size': (640, 360), 'default': True},
        {'timestamp': 15, 'size': (640, 360), 'default': False},
        {'timestamp': 30, 'size': (640, 360), 'default': False},
    ]
    
    for config in thumbnail_configs:
        thumbnail_filename = f"{video.id}_thumb_{config['timestamp']}s.jpg"
        thumbnail_path = os.path.join(thumbnails_dir, thumbnail_filename)
        
        try:
            (
                ffmpeg
                .input(input_path, ss=config['timestamp'])
                .filter('scale', config['size'][0], config['size'][1])
                .output(thumbnail_path, vframes=1)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            # Create VideoThumbnail object
            with open(thumbnail_path, 'rb') as f:
                thumb_file = File(f, name=thumbnail_filename)
                VideoThumbnail.objects.create(
                    video=video,
                    image=thumb_file,
                    size=f"{config['size'][0]}x{config['size'][1]}",
                    is_default=config['default']
                )
        
        except ffmpeg.Error as e:
            logger.error(f"Thumbnail generation error: {e.stderr.decode()}")
            continue