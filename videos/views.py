from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Video
from .serializers import VideoSerializer
from users.permissions import IsAdmin, IsResourceOwner, IsAdminOrResourceOwner
from django.db import models


class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer

    def get_permissions(self):
        if self.action == "list" or self.action == "retrieve":
            # Anyone can view videos
            permission_classes = [permissions.AllowAny]
        elif self.action == "create":
            # Only admins and creators can create videos
            permission_classes = [
                permissions.IsAuthenticated,
                (IsAdmin | IsResourceOwner),
            ]
        elif self.action in ["update", "partial_update", "destroy"]:
            # Admins can edit any video, creators can only edit their own
            permission_classes = [permissions.IsAuthenticated, IsAdminOrResourceOwner]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(uploader=self.request.user)

    def get_queryset(self):
        """
        Filter videos based on user role and ownership:
        - Admins see all videos
        - Creators see their own videos and all public videos
        - Viewers see all public videos
        """
        user = self.request.user

        # If user is not authenticated, return only public videos
        if not user.is_authenticated:
            return Video.objects.filter(status="public")

        # Admin can see all videos
        if user.role == "admin":
            return Video.objects.all()

        # Creator can see their own videos (any status) and public videos
        if user.role == "creator":
            return Video.objects.filter(
                models.Q(uploader=user) | models.Q(status="public")
            )

        # Viewers and guests see only public videos
        return Video.objects.filter(status="public")

    def update(self, request, *args, **kwargs):
        video = self.get_object()
        # Only allow users to update their own videos
        if video.uploader != request.user:
            return Response(
                {"detail": "You do not have permission to edit this video."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        video = self.get_object()
        # Only allow users to delete their own videos
        if video.uploader != request.user:
            return Response(
                {"detail": "You do not have permission to delete this video."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)
