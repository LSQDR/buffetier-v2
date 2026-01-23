"""
Google Cloud Storage helper for menu image uploads.
Handles image optimization, upload, and deletion.
"""

from google.cloud import storage
import os
from werkzeug.utils import secure_filename
from PIL import Image
import io

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
        # Open and optimize image
        img = Image.open(file)
        
        # Convert RGBA/LA to RGB
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Resize if too large
        img.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
        
        # Save to bytes buffer
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85, optimize=True)
        buffer.seek(0)
        
        # Upload to Cloud Storage
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        
        # Generate unique blob name
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        blob_name = f"menu-items/{timestamp}_{filename}"
        blob = bucket.blob(blob_name)
        
        # Upload with caching headers
        blob.upload_from_file(
            buffer,
            content_type='image/jpeg',
            rewind=True
        )
        
        # Make publicly accessible
        blob.make_public()
        
        return blob.public_url
        
    except Exception as e:
        raise Exception(f"Upload failed: {str(e)}")


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
        blob_name = image_url.split(f'{BUCKET_NAME}/')[-1]
        
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_name)
        
        blob.delete()
        return True
        
    except Exception as e:
        print(f"Delete error: {e}")
        return False
