import os
import json
import csv
from datetime import datetime
from tkinter import filedialog
from PIL import Image, ImageDraw
from managers.excel_manager import ExcelManager
import logging

class FileManager:
    """
    Manager for file operations including loading, saving, configuration, and logging.
    """
    def __init__(self):
        # Paths
        self.source_folder = ""
        self.destination_folder = ""
        
        # Configuration file
        self.config_file = "bug_validator_config.json"
        
        # Create Excel Manager
        self.excel_manager = ExcelManager()
    
    def load_config(self):
        """Load configuration from file"""
        config = {}
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.source_folder = config.get('source_folder', '')
                    self.destination_folder = config.get('destination_folder', '')
        except Exception as e:
            print(f"Error loading config: {e}")
        
        return config
    
    def save_config(self, source_folder=None, destination_folder=None):
        """Save configuration to file"""
        if source_folder:
            self.source_folder = source_folder
        if destination_folder:
            self.destination_folder = destination_folder
            
        try:
            config = {
                'source_folder': self.source_folder,
                'destination_folder': self.destination_folder
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def select_source_folder(self):
        """Open dialog to select source folder"""
        folder = filedialog.askdirectory(title="Select Source Folder with Images")
        if folder:
            self.source_folder = folder
            return folder
        return None
    
    def select_destination_folder(self):
        """Open dialog to select destination folder"""
        folder = filedialog.askdirectory(title="Select Destination Folder")
        if folder:
            self.destination_folder = folder
            return folder
        return None
    
    def check_folders(self):
        """Check if source and destination folders are set"""
        return bool(self.source_folder) and bool(self.destination_folder)
    
    def get_image_files(self):
        """Get list of image files from source folder"""
        if not self.source_folder:
            return []
        
        # Supported image extensions
        image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        
        # Get files with supported extensions
        image_files = [f for f in os.listdir(self.source_folder) 
                      if f.lower().endswith(image_extensions)]
        
        return image_files
    
    def save_image_with_defect(self, original_image, defect, original_filename, result_text=""):
        """Save an image with the specified defect (containing multiple rectangles)"""
        logger = logging.getLogger("bug_validator")
        
        if not original_image or not defect:
            logger.error(f"Missing original image or defect data")
            return False, "Missing image or defect data"
        
        # Check if the defect has any rectangles
        if not defect.get("rectangles") or len(defect["rectangles"]) == 0:
            logger.warning(f"No rectangles found in defect: {defect['name']}")
            return False, "No rectangles found in defect"
        
        # Log defect details for debugging
        logger.info(f"Saving defect: {defect['name']}, Rectangle count: {len(defect['rectangles'])}")
        
        # Create a copy of the original image to draw on
        output_image = original_image.copy()
        
        # Check if the image supports transparency
        if output_image.mode != 'RGBA' and output_image.mode != 'RGB':
            output_image = output_image.convert('RGBA')
            
        draw = ImageDraw.Draw(output_image, 'RGBA')  # Use RGBA mode for transparency
        
        # Draw all rectangles for this defect
        rectangles_drawn = 0
        for i, rectangle in enumerate(defect["rectangles"]):
            # Get the rectangle coordinates
            coords = rectangle["coords"]
            
            # Log rectangle info for debugging
            logger.debug(f"Processing rectangle {i+1} with coords: {coords}")
            
            # Ensure coords are in the correct format and contain valid values
            if not coords or len(coords) != 4:
                logger.warning(f"Invalid coordinates: {coords}")
                continue
                
            # Ensure the coordinates are properly ordered (x1 < x2, y1 < y2)
            x1, y1, x2, y2 = coords
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)
            
            # Ensure coordinates are within the image bounds
            img_width, img_height = original_image.size
            x1 = max(0, min(x1, img_width-1))
            y1 = max(0, min(y1, img_height-1))
            x2 = max(0, min(x2, img_width-1))
            y2 = max(0, min(y2, img_height-1))
            
            # Draw the rectangle with sanitized coordinates
            draw.rectangle([x1, y1, x2, y2], fill=(255, 255, 0, 90), outline=(255, 255, 0, 255))
            rectangles_drawn += 1
        
        # If no rectangles were drawn, return false
        if rectangles_drawn == 0:
            logger.warning(f"No valid rectangles to draw for defect: {defect['name']}")
            return False, "No valid rectangles to draw"
        
        # CSV log path
        csv_path = os.path.join(self.destination_folder, "validation_log.csv")
        csv_exists = os.path.exists(csv_path)
        
        # Get new filename for this defect
        new_filename = defect["rename"]
        if not new_filename:
            logger.warning(f"No rename value for defect: {defect['name']}")
            return False, "No rename value for defect"
            
        # Process the filename to include custom suffix if present
        # Format is "filename_number:custom_suffix"
        if ":" in new_filename:
            # Split at the colon to get the custom suffix
            new_filename = new_filename.replace(":", "_")
        
        # Add extension from original file
        _, ext = os.path.splitext(original_filename)
        new_filepath = os.path.join(self.destination_folder, new_filename + ext)
        
        # Save the image
        try:
            output_image.save(new_filepath)
            logger.info(f"Saved image to {new_filepath}")
            
            # Record in CSV log
            with open(csv_path, 'a', newline='') as csvfile:
                csv_writer = csv.writer(csvfile)
                
                # Write header if file is new
                if not csv_exists:
                    csv_writer.writerow([
                        "Date", "Time", "Original Filename", "New Filename", 
                        "Defect Name", "Rectangle Count in Defect"
                    ])
                
                # Write data for the defect
                now = datetime.now()
                # Get base filename without extension for both original and new filenames
                original_base_filename, _ = os.path.splitext(original_filename)
                csv_writer.writerow([
                    now.strftime("%Y-%m-%d"),
                    now.strftime("%H:%M:%S"),
                    original_base_filename,
                    new_filename,  # Already without extension
                    defect["name"],
                    rectangles_drawn  # Number of rectangles actually drawn
                ])
            
            # Update Excel file with results using the Excel Manager
            excel_success, excel_error = self.excel_manager.save_defect_result(self.destination_folder, new_filename + ext, result_text)
            if not excel_success:
                logger.error(f"Excel error: {excel_error}")
                return False, excel_error
            
            return True, ""
            
        except Exception as e:
            error_msg = f"Failed to save {new_filename + ext}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg 