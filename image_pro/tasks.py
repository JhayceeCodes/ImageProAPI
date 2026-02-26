from celery import shared_task
from PIL import Image as PILImage, ImageFilter
from django.core.files.base import ContentFile
from io import BytesIO
from .models import Image



@shared_task
def process_image_task(image_id):
    try:
        image_obj = Image.objects.get(id=image_id)
        image_obj.status = "processing"
        image_obj.save(update_fields=["status"])

        img = PILImage.open(image_obj.original_image.path)

        operations = image_obj.operations.all().order_by("created_at")

        quality = 85  # default quality

        for operation in operations:
            op_type = operation.operation_type
            params = operation.parameters

            # Resize
            if op_type == "resize":
                width = params.get("width")
                height = params.get("height")

                if width and height:
                    img = img.resize((int(width), int(height)))

            # Compress
            elif op_type == "compress":
                quality = params.get("quality", 85)


            # Filter
            elif op_type == "filter":
                filter_type = params.get("type")

                if filter_type == "grayscale":
                    img = img.convert("L")
                elif filter_type == "blur":
                    img = img.filter(ImageFilter.BLUR)
                elif filter_type == "sharpen":
                    img = img.filter(ImageFilter.SHARPEN)

            # Convert format
            elif op_type == "convert":
                new_format = params.get("format")
                if new_format:
                    image_obj.image_format = new_format.lower()

        
        output = BytesIO()

        img.save(
            output,
            format=image_obj.image_format.upper(),
            quality=quality
        )

        image_obj.processed_image.save(
            f"processed_{image_obj.id}.{image_obj.image_format}",
            ContentFile(output.getvalue()),
            save=False
        )

        image_obj.status = "completed"
        image_obj.save(update_fields=["processed_image", "status"])

    except Exception as e:
        image_obj.status = "failed"
        image_obj.save(update_fields=["status"])
        raise e