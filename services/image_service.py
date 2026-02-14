from PIL import Image
import os
import uuid
from werkzeug.utils import secure_filename

class ImageService:
    def __init__(self):
        self.upload_folder = 'uploads'
        self.allowed_extensions = {'png', 'jpg', 'jpeg', 'webp'}
        self.max_size = (800, 800)  # Max dimensions
        
        # Create upload folder if doesn't exist
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def allowed_file(self, filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def process_image(self, file):
        """Process uploaded image: validate, resize, optimize"""
        if not file or not self.allowed_file(file.filename):
            raise ValueError('Invalid file type. Allowed: PNG, JPG, JPEG, WebP')
        
        # Generate unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(self.upload_folder, filename)
        
        # Save temporarily
        file.save(filepath)
        
        # Open and process image
        try:
            img = Image.open(filepath)
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Resize if too large
            img.thumbnail(self.max_size, Image.Resampling.LANCZOS)
            
            # Save optimized
            img.save(filepath, optimize=True, quality=85)
            
            return filepath, filename
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(filepath):
                os.remove(filepath)
            raise Exception(f'Image processing failed: {str(e)}')
    
    def cleanup(self, filepath):
        """Delete temporary file after upload"""
        if os.path.exists(filepath):
            os.remove(filepath)
