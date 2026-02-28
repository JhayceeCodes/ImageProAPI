import json
from rest_framework import serializers
from rest_framework.reverse import reverse
from PIL import Image as PILImage
from django.utils import timezone
from datetime import timedelta
from .models import Image, ImageOperation


class ImageOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageOperation
        fields = ["operation_type", "parameters"]

    def validate(self, data):
        op_type = data["operation_type"]
        params = data["parameters"]

        if op_type == "resize":
            if "width" not in params or "height" not in params:
                raise serializers.ValidationError(
                    "Resize requires width and height."
                )

        if op_type == "compress":
            if "quality" not in params:
                raise serializers.ValidationError(
                    "Compress requires quality."
                )

        if op_type == "filter":
            allowed_filters = ["grayscale", "blur", "sharpen"]
            filter_type = params.get("type")
            if filter_type not in allowed_filters:
                raise serializers.ValidationError(
                    f"Invalid filter '{filter_type}'. Allowed: {', '.join(allowed_filters)}"
                )
        
        if op_type == "convert":
            allowed_formats = ["jpg", "png", "webp"]
            new_format = params.get("format")
            if not new_format:
                raise serializers.ValidationError(
                    "Convert requires a target 'format'."
                )
            if new_format.lower() not in allowed_formats:
                raise serializers.ValidationError(
                    f"Invalid format '{new_format}'. Allowed: {', '.join(allowed_formats)}"
                )

        return data


class ImageUploadSerializer(serializers.ModelSerializer):
    operations = serializers.CharField(write_only=True)
    detail_url = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = [
            "id",
            "original_image",
            "image_format",
            "operations",
            "status",
            "detail_url",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at", "detail_url"]
    
    def get_detail_url(self, obj):
        request = self.context.get("request")
        return reverse(
            "images-detail",
            kwargs={"pk": obj.pk},
            request=request
        )

    def validate_operations(self, value):
        try:
            operations = json.loads(value)
        except json.JSONDecodeError:
            raise serializers.ValidationError("Invalid JSON format for operations.")

        if not isinstance(operations, list):
            raise serializers.ValidationError("Operations must be a list.")

        validated_operations = []

        for index, operation in enumerate(operations):
            serializer = ImageOperationSerializer(data=operation)

            try:
                serializer.is_valid(raise_exception=True)
            except serializers.ValidationError as e:
                raise serializers.ValidationError({
                    f"operation_{index}": e.detail
                })

            validated_operations.append(serializer.validated_data)

        return validated_operations

    def validate(self, data):
        request = self.context["request"]
        operations = data.get("operations", [])
        image_file = data.get("original_image")

        # File size
        if image_file:
            max_size = 10 * 1024 * 1024 if request.user.is_authenticated else 2 * 1024 * 1024
            if image_file.size > max_size:
                raise serializers.ValidationError(
                    f"File size exceeds allowed limit ({max_size // (1024 * 1024)}MB)."
                )

        # Compression quality
        for op in operations:
            if op["operation_type"] == "compress":
                quality = op["parameters"].get("quality")
                if request.user.is_authenticated:
                    if quality < 10 or quality > 95:
                        raise serializers.ValidationError("Authenticated users: quality must be 10-95")
                else:
                    if quality < 40 or quality > 80:
                        raise serializers.ValidationError("Anonymous users: quality must be 40-80")

        # Anonymous users operation limit
        if not request.user.is_authenticated and len(operations) > 2:
            raise serializers.ValidationError("Anonymous users can only perform 2 operations")

        return data

    def create(self, validated_data):
        operations_data = validated_data.pop("operations", [])
        request = self.context["request"]

        image = Image.objects.create(
            user=request.user if request.user.is_authenticated else None,
            is_anonymous=not request.user.is_authenticated,
            status="pending",
            download_expires_at=timezone.now() + timedelta(hours=24),  #auto expiry in 24hrs
            **validated_data
        )
        for op_data in operations_data:
            ImageOperation.objects.create(
                image=image,
                **op_data
            )


        from .tasks import process_image_task
        process_image_task.delay(image.id)

        return image

class ImageDetailSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()
    seconds_remaining = serializers.SerializerMethodField()
    class Meta:
        model = Image
        fields = [
            "id",
            "status",
            "image_format",
            "estimated_ready_at",
            "seconds_remaining",
            "download_url",
            "created_at",
        ]

    def get_download_url(self, obj):
        request = self.context.get("request")

        if obj.status == "completed":
            return reverse(
                "images-download",
                kwargs={"pk": obj.pk},
                request=request
            )

        return None
    

    def get_seconds_remaining(self, obj):
        if obj.status == "pending":
            return 8

        if obj.status == "processing" and obj.estimated_ready_at:
            remaining = obj.estimated_ready_at - timezone.now()
            return max(int(remaining.total_seconds()), 0)

        return None
