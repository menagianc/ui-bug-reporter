import os
import json
import csv
from datetime import datetime
from tkinter import filedialog
from PIL import Image, ImageDraw
import openpyxl
from openpyxl import Workbook
from managers.excel_manager import ExcelManager

class FileManager:
    """
    Manager for file operations including loading, saving, configuration, and logging.
    """
    def __init__(self):
        # Paths
        self.source_folder = ""
        self.destination_folder = ""
        
        # Categories
        self.categories = ["Bug for current Project", "Bug for other Project", "No defects found"]
        
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
        """Open dialog to select destination folder and create category folders"""
        folder = filedialog.askdirectory(title="Select Destination Base Folder")
        if folder:
            self.destination_folder = folder
            
            # Create category subfolders
            for category in self.categories:
                category_folder = os.path.join(folder, category.replace(" ", "_"))
                os.makedirs(category_folder, exist_ok=True)
            
            return folder
        return None
    
    def get_categories(self):
        """Get available categories"""
        return self.categories
    
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
        if not original_image or not defect:
            print(f"Missing original image or defect data")
            return False
        
        # Check if the defect has any rectangles
        if not defect.get("rectangles") or len(defect["rectangles"]) == 0:
            print(f"No rectangles found in defect: {defect['name']}")
            return False
        
        # Log defect details for debugging
        print(f"Saving defect: {defect['name']}, Category: {defect['category']}, Rectangle count: {len(defect['rectangles'])}")
        
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
            print(f"Processing rectangle {i+1} with coords: {coords}")
            
            # Ensure coords are in the correct format and contain valid values
            if not coords or len(coords) != 4:
                print(f"Invalid coordinates: {coords}")
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
            return False
        
        # CSV log path
        csv_path = os.path.join(self.destination_folder, "validation_log.csv")
        csv_exists = os.path.exists(csv_path)
        
        # Get category and create path
        category = defect["category"]
        category_folder = os.path.join(self.destination_folder, category.replace(" ", "_"))
        
        # Create the folder if it doesn't exist
        os.makedirs(category_folder, exist_ok=True)
        
        # Get new filename for this defect
        new_filename = defect["rename"]
        if not new_filename:
            return False
        
        # Add extension from original file
        _, ext = os.path.splitext(original_filename)
        new_filepath = os.path.join(category_folder, new_filename + ext)
        
        # Save the image
        try:
            output_image.save(new_filepath)
            
            # Record in CSV log
            with open(csv_path, 'a', newline='') as csvfile:
                csv_writer = csv.writer(csvfile)
                
                # Write header if file is new
                if not csv_exists:
                    csv_writer.writerow([
                        "Date", "Time", "Original Filename", "New Filename", "Category", 
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
                    category,
                    defect["name"],
                    rectangles_drawn  # Number of rectangles actually drawn
                ])
            
            # Update Excel file with results using the Excel Manager
            self.excel_manager.save_defect_result(category_folder, new_filename + ext, result_text)
            
            return True
            
        except Exception as e:
            print(f"Failed to save {new_filename + ext}: {str(e)}")
            return False 