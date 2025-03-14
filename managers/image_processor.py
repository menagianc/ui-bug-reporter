import os
from PIL import Image, ImageTk

class ImageProcessor:
    """
    Manager for image processing operations including loading, resizing, and coordinate conversion.
    """
    def __init__(self):
        # Image data
        self.image_files = []
        self.source_folder = ""
        self.current_index = 0
        self.current_filename = ""
        
        # Image objects
        self.original_image = None
        self.displayed_image = None
        self.photo_image = None
        
        # Zoom level (1.0 = 100%)
        self.zoom_level = 1.0
    
    def set_image_files(self, image_files, source_folder):
        """Set the list of available image files"""
        self.image_files = image_files
        self.source_folder = source_folder
    
    def load_image(self, index):
        """Load image at specified index"""
        if not self.image_files or not (0 <= index < len(self.image_files)):
            return False
        
        self.current_index = index
        self.current_filename = self.image_files[index]
        self.zoom_level = 1.0  # Reset zoom level for new image
        
        try:
            image_path = os.path.join(self.source_folder, self.current_filename)
            self.original_image = Image.open(image_path)
            
            # Don't resize here - wait for canvas dimensions
            # The UI manager will call resize_image with canvas dimensions
            return True
        except Exception as e:
            print(f"Error loading image: {e}")
            return False
    
    def resize_image(self, canvas_width, canvas_height):
        """Resize image to fit canvas while maintaining aspect ratio"""
        if not self.original_image:
            return False
        
        # Get image dimensions
        img_width, img_height = self.original_image.size
        
        # Calculate scaling factor to fit in canvas
        fit_ratio = min(canvas_width / img_width, canvas_height / img_height)
        
        # Apply zoom level to the scaling ratio
        effective_ratio = fit_ratio * self.zoom_level
        
        # Calculate new dimensions with zoom applied
        new_width = int(img_width * effective_ratio)
        new_height = int(img_height * effective_ratio)
        
        # Resize and update display image
        self.displayed_image = self.original_image.copy().resize((new_width, new_height))
        self.photo_image = ImageTk.PhotoImage(self.displayed_image)
        
        return True
    
    def zoom_in(self, canvas_width, canvas_height):
        """Increase zoom level"""
        if not self.original_image:
            return False
            
        self.zoom_level = min(2.0, self.zoom_level + 0.1)
        return self.resize_image(canvas_width, canvas_height)
    
    def zoom_out(self, canvas_width, canvas_height):
        """Decrease zoom level"""
        if not self.original_image:
            return False
            
        # Don't allow zooming out too much - minimum is to fit the whole image
        self.zoom_level = max(0.1, self.zoom_level - 0.1)
        return self.resize_image(canvas_width, canvas_height)
    
    def reset_zoom(self, canvas_width, canvas_height):
        """Reset zoom to fit the whole image"""
        if not self.original_image:
            return False
            
        self.zoom_level = 1.0
        return self.resize_image(canvas_width, canvas_height)
    
    def canvas_to_image_coords(self, canvas_coords, canvas_dimensions):
        """Convert canvas coordinates to original image coordinates"""
        if not self.original_image or not canvas_coords:
            return None
        
        # Unpack coordinates
        canvas_x1, canvas_y1, canvas_x2, canvas_y2 = canvas_coords
        canvas_width, canvas_height = canvas_dimensions
        
        # Get image dimensions
        img_width, img_height = self.original_image.size
        
        # Calculate scaling factor based on zoom level and fit-to-canvas ratio
        fit_ratio = min(canvas_width / img_width, canvas_height / img_height)
        scale_x = 1.0 / (fit_ratio * self.zoom_level)
        scale_y = 1.0 / (fit_ratio * self.zoom_level)
        
        # Convert to original image coordinates
        orig_x1 = int(canvas_x1 * scale_x)
        orig_y1 = int(canvas_y1 * scale_y)
        orig_x2 = int(canvas_x2 * scale_x)
        orig_y2 = int(canvas_y2 * scale_y)
        
        return (orig_x1, orig_y1, orig_x2, orig_y2)
    
    def image_to_canvas_coords(self, image_coords, canvas_dimensions):
        """Convert original image coordinates to canvas coordinates"""
        if not self.original_image or not image_coords:
            return None
        
        # Unpack coordinates
        img_x1, img_y1, img_x2, img_y2 = image_coords
        canvas_width, canvas_height = canvas_dimensions
        
        # Get image dimensions
        img_width, img_height = self.original_image.size
        
        # Calculate scaling factor based on zoom level and fit-to-canvas ratio
        fit_ratio = min(canvas_width / img_width, canvas_height / img_height)
        scale_x = fit_ratio * self.zoom_level
        scale_y = fit_ratio * self.zoom_level
        
        # Convert to canvas coordinates
        canvas_x1 = int(img_x1 * scale_x)
        canvas_y1 = int(img_y1 * scale_y)
        canvas_x2 = int(img_x2 * scale_x)
        canvas_y2 = int(img_y2 * scale_y)
        
        return (canvas_x1, canvas_y1, canvas_x2, canvas_y2)
    
    def get_image_dimensions(self):
        """Get dimensions of the original image"""
        if self.original_image:
            return self.original_image.size
        return (0, 0)
    
    def get_current_filename_parts(self):
        """Get filename and extension of current image"""
        if self.current_filename:
            return os.path.splitext(self.current_filename)
        return ("", "")
    
    def get_original_image(self):
        """Get the original image object"""
        return self.original_image
    
    def get_current_filename(self):
        """Get the current image filename"""
        return self.current_filename
    
    def has_current_image(self):
        """Check if a current image is loaded"""
        return self.original_image is not None 