from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


def default_expiry():
    return timezone.now() + timedelta(minutes=5)
class Image(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )

    IMAGE_FORMAT_CHOICES = (
        ("jpg", "JPEG"),
        ("png", "PNG"),
        ("webp", "WebP")
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="images", null=True, blank=True)
    original_image = models.ImageField(upload_to="images/originals/")
    processed_image = models.ImageField(upload_to="images/processed/", null=True, blank=True)
    image_format = models.CharField(max_length=4, choices=IMAGE_FORMAT_CHOICES)
    is_anonymous = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    download_expires_at = models.DateTimeField(default=default_expiry)

    def __str__(self):
        return f"Image {self.id}"




class ImageOperation(models.Model):
    OPERATION_TYPE_CHOICES = (
        ("resize", "Resize"),
        ("convert", "Convert"),
        ("filter", "Filter"),
        ("compress", "Compress")
    )

    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name="operations")
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPE_CHOICES, default="resize")
    parameters = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.operation_type} on Image {self.image.id}"


