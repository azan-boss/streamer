from rest_framework import serializers
from .models import Video


class VideoSerializer(serializers.ModelSerializer):
    uploader_username = serializers.ReadOnlyField(source="uploader.username")
    is_owner = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            "id",
            "title",
            "description",
            "file",
            "thumbnail",
            "uploader",
            "uploader_username",
            "upload_date",
            "views_count",
            "likes_count",
            "duration",
            "status",
            "is_owner",
        ]
        read_only_fields = ["uploader", "upload_date", "views_count", "likes_count"]

    def get_is_owner(self, obj):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            return obj.uploader == request.user
        return False

    def get_is_admin(self, obj):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            return request.user.is_superuser
        return False
