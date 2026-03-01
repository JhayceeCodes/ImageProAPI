
from io import BytesIO
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.db.models import Avg, F, ExpressionWrapper, DurationField
from django.core.files.base import ContentFile
from PIL import Image as PILImage, ImageFilter
from .models import Image




@shared_task
def process_image_task(image_id):
    image_obj = None

    try:
        image_obj = Image.objects.get(id=image_id)
        now = timezone.now()
        image_obj.status = "processing"
        image_obj.processing_started_at = now

        recent_images = (
            Image.objects
            .filter(
                status="completed",
                processing_started_at__isnull=False,
                processing_completed_at__isnull=False
            )
            .order_by("-processing_completed_at")[:10]
            .annotate(
                duration=ExpressionWrapper(
                    F("processing_completed_at") - F("processing_started_at"),
                    output_field=DurationField()
                )
            )
        )

        average_duration = recent_images.aggregate(
            avg_duration=Avg("duration")
        )["avg_duration"]

        if average_duration:
            image_obj.estimated_ready_at = now + average_duration
        else:
            image_obj.estimated_ready_at = now + timedelta(seconds=8)

        image_obj.save(update_fields=[
            "status",
            "processing_started_at",
            "estimated_ready_at"
        ])

    
        img = PILImage.open(image_obj.original_image)
        operations = image_obj.operations.all().order_by("created_at")

        quality = 85  # default quality

        #operations
        for operation in operations:
            op_type = operation.operation_type
            params = operation.parameters

            if op_type == "resize":
                width = params.get("width")
                height = params.get("height")

                if width and height:
                    img = img.resize((int(width), int(height)))

            elif op_type == "compress":
                quality = params.get("quality", 85)

            elif op_type == "filter":
                filter_type = params.get("type")

                if filter_type == "grayscale":
                    img = img.convert("L")
                elif filter_type == "blur":
                    img = img.filter(ImageFilter.BLUR)
                elif filter_type == "sharpen":
                    img = img.filter(ImageFilter.SHARPEN)

            elif op_type == "convert":
                new_format = params.get("format")
                if new_format:
                    image_obj.image_format = new_format.lower()

    
        FORMAT_MAP = {
            "jpg": "JPEG",
            "jpeg": "JPEG",
            "png": "PNG",
            "webp": "WEBP",
        }

        format_name = FORMAT_MAP.get(
            image_obj.image_format.lower(),
            image_obj.image_format.upper()
        )

        #save processed image
        output = BytesIO()

        img.save(
            output,
            format=format_name,
            quality=quality
        )

        image_obj.processed_image.save(
            f"processed_{image_obj.id}.{image_obj.image_format}",
            ContentFile(output.getvalue()),
            save=False
        )


        image_obj.status = "completed"
        image_obj.processing_completed_at = timezone.now()
        image_obj.estimated_ready_at = None

        image_obj.save(update_fields=[
            "processed_image",
            "status",
            "processing_completed_at",
            "estimated_ready_at"
        ])

    except Exception as e:
        if image_obj:
            image_obj.status = "failed"
            image_obj.estimated_ready_at = None
            image_obj.save(update_fields=["status", "estimated_ready_at"])

        raise e




@shared_task
def delete_expired_images():
    now = timezone.now()
    expired_images = Image.objects.filter(
        download_expires_at__lte=now
    )

    for img in expired_images:

        if img.original_image:
            img.original_image.delete(save=False)

        if img.processed_image:
            img.processed_image.delete(save=False)

        img.delete()