import boto3
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import FileResponse
from datetime import timedelta
from .models import Image
from .serializers import ImageUploadSerializer, ImageDetailSerializer
from .utils import mark_download_expiry


class ImageViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Image.objects.all()

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
        # image = get_object_or_404(self.get_queryset(), pk=pk)
        try:
            image = Image.objects.get(pk=pk)
        except Image.DoesNotExist:
            return Response({"error": "No Image matches the given query."}, status=status.HTTP_404_NOT_FOUND)

        # permission check
        if request.user.is_authenticated:
            if image.user != request.user:
                return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
        else:
            if not image.is_anonymous:
                return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
            
            if not image.is_anonymous:
                if request.user != image.user:
                    return Response(
                        {"error": "Unauthorized"},
                        status=status.HTTP_403_FORBIDDEN
                    )

        if image.status != "completed":
            return Response(
                {"error": "Image not ready"},
                status=status.HTTP_400_BAD_REQUEST
            )

        now = timezone.now()

        if image.download_expires_at and now > image.download_expires_at:
            return Response({"error": "Download expired"}, status=status.HTTP_403_FORBIDDEN)


        """#expiry check
        if image.download_expires_at:
            if now > image.download_expires_at:
                return Response(
                    {"error": "Download expired"},
                    status=status.HTTP_403_FORBIDDEN
                )

        if not image.download_expires_at:
            image.download_expires_at = timezone.now() + (
                timedelta(minutes=2) if request.user.is_authenticated else timedelta(minutes=5)
            ) #expiry upon download
            image.save(update_fields=["download_expires_at"])"""
        
        mark_download_expiry(image)

        #displays image in browser directly from s3 bucket
        """signed_url = image.processed_image.url

        return Response({
            "download_url": signed_url
        })"""

        #automatically download image from s3
        s3 = boto3.client("s3")
        bucket_name = image.processed_image.storage.bucket_name
        key = image.processed_image.name

        try:
            s3_object = s3.get_object(Bucket=bucket_name, Key=key)
            response = FileResponse(
                s3_object['Body'],
                content_type="application/octet-stream"
            )
            response['Content-Disposition'] = f'attachment; filename="{key.split("/")[-1]}"'
            return response
        except s3.exceptions.NoSuchKey:
            return Response({"error": "File not found in S3"}, status=status.HTTP_404_NOT_FOUND)
        

    