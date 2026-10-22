"""
Google Cloud Storage helper for menu image uploads.
Handles image optimization, upload, and deletion.
"""

import io
import os

from google.cloud import storage
from PIL import Image
from werkzeug.utils import secure_filename

BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME', 'buffetier-menu-images')
MAX_IMAGE_SIZE = (1024, 1024)  # Max dimensions

def upload_menu_image(file):
    """
    Upload and optimize menu item image to Cloud Storage.

    Args:
        file: FileStorage object from Flask request

    Returns:
        str: Public URL of uploaded image

    Raises:
        ValueError: If file type is invalid
        Exception: If upload fails
    """
    # Validate file extension
    allowed_extensions = {'png', 'jpg', 'jpeg', 'webp'}
    filename = secure_filename(file.filename)

    if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        raise ValueError('Invalid file type. Use PNG, JPG, JPEG, or WebP')

    try:
        # Read file into memory first
        file_content = file.read()
        file_stream = io.BytesIO(file_content)

        # Open and optimize image
        img = Image.open(file_stream)

        # Convert RGBA/LA to RGB
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            if img.mode in ('RGBA', 'LA'):
                background.paste(img, mask=img.split()[-1])
                img = background
            else:
                img = img.convert('RGB')

        # Resize if too large
        if img.width > MAX_IMAGE_SIZE[0] or img.height > MAX_IMAGE_SIZE[1]:
            img.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)

        # Save to bytes buffer
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85, optimize=True)
        buffer.seek(0)

        # Upload to Cloud Storage
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)

        # Generate unique blob name with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = filename.rsplit('.', 1)[0]
        blob_name = f"menu-items/{timestamp}_{base_name}.jpg"
        blob = bucket.blob(blob_name)

        # Upload with proper content type and caching
        blob.upload_from_file(
            buffer,
            content_type='image/jpeg',
            rewind=True
        )

        # Make publicly accessible
        blob.make_public()

        return blob.public_url

    except Exception as e:
        # More detailed error for debugging
        import traceback
        error_details = traceback.format_exc()
        print(f"Upload error details: {error_details}")
        raise Exception(f"Upload failed: {str(e)}") from e


def delete_menu_image(image_url):
    """
    Delete image from Cloud Storage.

    Args:
        image_url: Full public URL of the image

    Returns:
        bool: True if deleted successfully
    """
    if not image_url or 'storage.googleapis.com' not in image_url:
        return False

    try:
        # Extract blob name from URL
        # URL format: https://storage.googleapis.com/bucket-name/blob-name
        parts = image_url.split(f'{BUCKET_NAME}/')
        if len(parts) < 2:
            return False

        blob_name = parts[-1]

        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_name)

        # Check if blob exists before deleting
        if blob.exists():
            blob.delete()
            return True
        else:
            print(f"Blob does not exist: {blob_name}")
            return False

    except Exception as e:
        print(f"Delete error: {e}")
        return False
