from rest_framework import serializers
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
    operation = ImageOperationSerializer(many=True, write_only=True)

    class Meta: 
        model = Image
        fields = [
            "id",
            "original_image",
            "image_format",
            "operations",
            "status",
            "created_at"
        ]
        read_only_fields = ["id", "status", "created_at"]



    def validate(self, data):
        request = self.context["request"]
        operations = data.get("operations", [])
        image_file = data.get("original_image")

        #file size
        if image_file:
            if request.user.is_authenticated:
                max_size = 10 * 1024 * 1024  
            else:
                max_size = 2 * 1024 * 1024   

            if image_file.size > max_size:
                raise serializers.ValidationError(
                    f"File size exceeds allowed limit ({max_size // (1024 * 1024)}MB)."
                )

        #compression limit
        for op in operations:
            if op["operation_type"] == "compress":
                quality = op["parameters"].get("quality")

                if request.user.is_authenticated:
                    if quality < 10 or quality > 95:
                        raise serializers.ValidationError(
                            "Authenticated users: quality must be 10-95"
                        )
                else:
                    if quality < 40 or quality > 80:
                        raise serializers.ValidationError(
                            "Anonymous users: quality must be 40-80"
                        )
                    
        if not request.user.is_authenticated and len(operations) > 2:
            raise serializers.ValidationError(
                "Anonymous users can only perform 2 operations"
            )


        return data
    
    def create(self, validated_data):
        operations_data = validated_data.pop("operations")
        request = self.context["request"]

        image = Image.objects.create(
            user=request.user if request.user.is_authenticated else None,
            is_anonymous=not request.user.is_authenticated,
            status="pending",
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
    class Meta:
        model = Image
        fields = [
            "id",
            "status",
            "image_format",
            "created_at",
            "download_url"
        ]

    def get_download_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(
            f"/api/images/{obj.id}/download/"
        )