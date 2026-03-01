import boto3
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import FileResponse
from datetime import timedelta
from .models import Image
from .serializers import ImageUploadSerializer, ImageDetailSerializer


class ImageViewSet(viewsets.ModelViewSet):
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
    
    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        image = get_object_or_404(self.get_queryset(), pk=pk)
        
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

        #expiry check
        if image.download_expires_at:
            if now > image.download_expires_at:
                return Response(
                    {"error": "Download expired"},
                    status=status.HTTP_403_FORBIDDEN
                )

        if not image.download_expires_at:
            image.download_expires_at = now + timedelta(minutes=5)
            image.save(update_fields=["download_expires_at"])

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