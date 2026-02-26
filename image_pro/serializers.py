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
            if "type" not in params:
                raise serializers.ValidationError(
                    "Filter requires type."
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
    class Meta:
        model = Image
        fields = [

        ]