import os
from cloudinary_storage.storage import MediaCloudinaryStorage


class MediaCloudinaryStorageWithType(MediaCloudinaryStorage):
    """
    Custom Cloudinary storage that automatically detects resource_type
    (image, video, raw) from the file extension.
    
    This allows a single storage backend to seamlessly handle:
    - Images (jpg, png, webp, etc.) -> Cloudinary image resource
    - Videos (mp4, webm, mov, etc.) -> Cloudinary video resource
    - Documents & files (pdf, docx, zip, etc.) -> Cloudinary raw resource
    """
    IMAGE_EXTENSIONS = {
        'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg', 'ico', 'tiff', 'tif', 'heic'
    }
    VIDEO_EXTENSIONS = {
        'mp4', 'webm', 'mov', 'avi', 'mkv', 'flv', 'wmv', 'm4v', '3gp', 'mp3', 'wav', 'ogg'
    }

    def _get_resource_type(self, name):
        ext = os.path.splitext(name)[1].lower().lstrip('.')
        if ext in self.IMAGE_EXTENSIONS:
            return 'image'
        elif ext in self.VIDEO_EXTENSIONS:
            return 'video'
        return 'raw'

