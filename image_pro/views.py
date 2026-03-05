import boto3
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import FileResponse
from .models import Image
from .serializers import ImageUploadSerializer, ImageDetailSerializer
from .utils import mark_download_expiry


class ImageViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Image.objects.all()
    http_method_names = ["get", "post"]

    def get_serializer_class(self):
        if self.action == "create":
            return ImageUploadSerializer
        return ImageDetailSerializer
    
    

    def get_queryset(self):
        user = self.request.user

        if user.is_authenticated:
            return Image.objects.filter(user=user)

        #none for anonymous users
        return Image.objects.none()
    

    def get_object(self):
        """
        Fetch an image for detail/download.
        Auth users: only their own images.
        Anonymous: only images marked is_anonymous=True.
        """
        queryset = Image.objects.all()  # ignore get_queryset for detail access
        obj = get_object_or_404(queryset, pk=self.kwargs["pk"])
        
        if self.request.user.is_authenticated:
            if obj.user != self.request.user:
                raise PermissionDenied("Unauthorized")
        else:
            if not obj.is_anonymous:
                raise PermissionDenied("Unauthorized")
        
        return obj
    
    
    
    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        """
        Download the processed image from S3 with permission and expiry checks.
        """
        image = self.get_object()  
        if image.status != "completed":
            return Response({"error": "Image not ready"}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()

        if image.download_expires_at and now > image.download_expires_at:
            return Response({"error": "Download expired"}, status=status.HTTP_403_FORBIDDEN)

        mark_download_expiry(image)
        
        try:
            file_handle = image.processed_image.open('rb')
        except Exception:
            return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)

        response = FileResponse(
            file_handle,
            content_type="application/octet-stream"
        )
        response['Content-Disposition'] = f'attachment; filename="{image.processed_image.name.split("/")[-1]}"'

        return response
        

    