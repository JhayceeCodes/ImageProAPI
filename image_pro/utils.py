from django.utils import timezone
from datetime import timedelta

def mark_download_expiry(image):
    """
    Set the download expiry after a download event.
    """
    if image.is_anonymous:
        image.download_expires_at = timezone.now() + timedelta(seconds=20)
    else:
        image.download_expires_at = timezone.now() + timedelta(minutes=5)
    image.save(update_fields=["download_expires_at"])