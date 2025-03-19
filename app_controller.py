import tkinter as tk
from managers.ui_manager import UIManager
from managers.image_processor import ImageProcessor
from managers.file_manager import FileManager
from managers.defect_manager import DefectManager
from managers.history_manager import HistoryManager
from managers.logger_manager import LoggerManager
from PIL import ImageDraw
import os
import copy
import csv
from datetime import datetime

class AppController:
    """
    Main controller class that coordinates all components of the application.
    """
    def __init__(self, root):
        # Initialize logger
        self.logger = LoggerManager(enabled=True, log_level=LoggerManager.DEBUG)
        self.logger.info("Initializing Bug Validator application")
        
        # Initialize the root window
        self.root = root
        self.root.title("Bug Validator")
        self.root.geometry("1200x800+50+50")
        
        # Set minimum window size to ensure UI elements have enough space
        self.root.minsize(900, 600)
        
        # Force an update to ensure window dimensions are correctly set
        self.root.update_idletasks()
        
        # Bind to window state changes
        self.root.bind("<Configure>", self._on_window_configure)
        
        # Create managers
        self.file_manager = FileManager()
        self.image_processor = ImageProcessor()
        self.defect_manager = DefectManager()
        self.history_manager = HistoryManager(max_history=20)
        
        # Pan variables
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.is_panning = False
        
        # Create UI last as it needs access to all other managers
        self.ui_manager = UIManager(self.root, self)
        
        # Load saved configuration
        self.load_config()
        
    def load_config(self):
        """Load configuration and set initial state"""
        config = self.file_manager.load_config()
        
        if config.get('source_folder') and config.get('destination_folder'):
            self.ui_manager.update_folder_paths(
                config.get('source_folder', ''),
                config.get('destination_folder', '')
            )
            self.load_images()
    
    def select_source_folder(self):
        """Handle source folder selection"""
        folder = self.file_manager.select_source_folder()
        if folder:
            self.ui_manager.update_source_path(folder)
            self.save_config()
    
    def select_destination_folder(self):
        """Handle destination folder selection"""
        folder = self.file_manager.select_destination_folder()
        if folder:
            self.ui_manager.update_destination_path(folder)
            self.save_config()
    
    def save_config(self):
        """Save current configuration"""
        self.file_manager.save_config(
            source_folder=self.file_manager.source_folder,
            destination_folder=self.file_manager.destination_folder
        )
    
    def load_images(self):
        """Load images from source folder"""
        if not self.file_manager.check_folders():
            return False
            
        image_files = self.file_manager.get_image_files()
        if not image_files:
            return False
            
        self.image_processor.set_image_files(image_files, self.file_manager.source_folder)
        self.load_image(0)
        return True
    
    def load_image(self, index, preserve_defects=False):
        """Load and display a specific image"""
        if not self.image_processor.load_image(index):
            return False
            
        # Reset states if not preserving defects from previous save operation
        if not preserve_defects:
            self.defect_manager.clear_defects()
            self.history_manager.clear_history()
            
            # Clear the results text field
            self.ui_manager.clear_result_text()
        
        # Resize the image to fit canvas
        canvas_dimensions = self.ui_manager.get_canvas_dimensions()
        if canvas_dimensions[0] > 1 and canvas_dimensions[1] > 1:
            self.image_processor.resize_image(*canvas_dimensions)
        
        # Update UI - This clears the canvas and redraws the image
        self.ui_manager.update_image_display(
            self.image_processor.photo_image,
            self.image_processor.current_filename,
            self.image_processor.current_index,
            len(self.image_processor.image_files)
        )
        
        # Make sure the canvas is updated
        self.ui_manager.canvas.update_idletasks()
        
        # Clear other UI elements
        self.ui_manager.clear_defects_list()
        self.ui_manager.clear_rectangles_list()
        
        if not preserve_defects:
            self.ui_manager.disable_defect_details()
            
            # Add initial empty state to history
            self.add_to_history()
            
            # Automatically create a default defect
            self._create_default_defect()
        
        return True
    
    def _create_default_defect(self):
        """Create a default defect automatically when loading an image"""
        if not self.image_processor.has_current_image():
            return
            
        # Create default defect name
        defect_name = "Defect 1"
        filename, _ = self.image_processor.get_current_filename_parts()
        
        # Add a new defect with no rectangles yet
        defect = self.defect_manager.add_defect(
            name=defect_name,
            rename=f"{filename}_1",  # Just use number without user text
            category=""
        )
        
        # Clear results text field
        self.ui_manager.clear_result_text()
        
        # Update UI
        self.ui_manager.add_defect_to_list(defect_name)
        self.ui_manager.select_defect(0)  # Select the first defect
        
        # Add to history
        self.add_to_history()
    
    def add_new_defect(self):
        """Create a new defect instance"""
        if not self.image_processor.has_current_image():
            self.ui_manager.show_info("Please load an image first.")
            return
        
        # Verify the currently selected defect has custom filename suffix and result text
        current_selected_index = self.defect_manager.get_selected_index()
        if current_selected_index >= 0:
            current_defect = self.defect_manager.get_defect(current_selected_index)
            current_results_text = self.ui_manager.get_result_text()
            
            # Save current results text to the current defect using dedicated method
            self.logger.debug(f"Before adding defect: Saving result text from defect {current_selected_index}: '{current_results_text}'")
            self.defect_manager.update_result_text(current_selected_index, current_results_text)
            
            # Check if there's a custom suffix (indicated by a colon in the rename field)
            has_custom_suffix = False
            if current_defect and "rename" in current_defect:
                # Check if there's a colon AND content after the colon
                if ":" in current_defect["rename"]:
                    suffix = current_defect["rename"].split(":", 1)[1]
                    has_custom_suffix = bool(suffix.strip())
            
            # Check if result text is empty
            if not current_results_text.strip():
                self.ui_manager.show_warning("Please fill in the Result field before creating a new defect.")
                return
                
            # Check if custom filename suffix is empty
            if not has_custom_suffix:
                self.ui_manager.show_warning("Please fill in the Custom Filename Suffix field before creating a new defect.")
                return
        
        # Clear ALL rectangles from canvas (both defect and drawing tags)
        self.ui_manager.canvas.delete("defect")
        self.ui_manager.canvas.delete("drawing")
        
        # Force canvas to refresh completely
        self.ui_manager.canvas.update_idletasks()
        self.ui_manager.canvas.update()  # Force a more complete update
        
        # Create new defect name
        defect_count = self.defect_manager.get_defect_count() + 1
        defect_name = f"Defect {defect_count}"
        filename, _ = self.image_processor.get_current_filename_parts()
        
        # Add a new defect with no rectangles yet, using sequential number
        defect = self.defect_manager.add_defect(
            name=defect_name,
            rename=f"{filename}_{defect_count}:",  # Add colon to indicate suffix is needed
            category=""
        )
        
        # Clear results text for the new defect
        self.ui_manager.clear_result_text()
        
        # UPDATE UI - Directly select the defect without triggering callbacks
        self.ui_manager.add_defect_to_list(defect_name)
        
        # Select the defect in the listbox without triggering _on_defect_selected
        new_index = self.defect_manager.get_defect_count() - 1
        self.defect_manager.select_defect(new_index)
        self.ui_manager.select_defect(new_index, trigger_callback=False)
        self.ui_manager.update_defect_details(
            defect['rename'],
            ""
        )
        self.ui_manager.enable_defect_details()
        
        # Add to history
        self.add_to_history()
    
    def start_draw(self, event):
        """Start drawing a defect rectangle"""
        if self.is_panning:
            return
        
        # Check if a defect is selected
        if self.defect_manager.get_selected_index() < 0:
            self.ui_manager.show_info("Please select a defect or create a new one first.")
            return
        
        self.ui_manager.start_draw(event)
    
    def draw(self, event):
        """Continue drawing a defect rectangle"""
        if self.is_panning:
            return
            
        self.ui_manager.draw(event)
    
    def stop_draw(self, event):
        """Finish drawing a defect rectangle"""
        if self.is_panning:
            return
            
        canvas_coords = self.ui_manager.stop_draw(event)
        if not canvas_coords:
            return
            
        # Convert canvas coords to image coords
        img_coords = self.image_processor.canvas_to_image_coords(
            canvas_coords,
            self.ui_manager.get_canvas_dimensions()
        )
        
        # Get the selected defect index
        defect_index = self.defect_manager.get_selected_index()
        if defect_index < 0:
            self.ui_manager.show_info("Please select a defect or create a new one first.")
            return
        
        # Add rectangle to the selected defect
        self.defect_manager.add_rectangle_to_defect(
            defect_index=defect_index,
            coords=img_coords,
            canvas_rect=self.ui_manager.rect_id
        )
        
        # Update the rectangles list
        self.ui_manager.update_rectangles_list(defect_index)
        
        # Select the newly added rectangle
        rectangles_count = self.defect_manager.get_rectangle_count_for_defect(defect_index)
        if rectangles_count > 0:
            self.defect_manager.select_rectangle(rectangles_count - 1)
            self.ui_manager.highlight_rectangle(defect_index, rectangles_count - 1)
        
        # Add to history
        self.add_to_history()
    
    def start_pan(self, event):
        """Start panning the image"""
        self.is_panning = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        # Set the scan mark at the start point
        self.ui_manager.start_canvas_scan(event.x, event.y)
    
    def pan(self, event):
        """Pan the image"""
        if not self.is_panning:
            return
            
        # Directly use the new position for scan_dragto
        self.ui_manager.continue_canvas_scan(event.x, event.y)
    
    def stop_pan(self, event):
        """Stop panning the image"""
        self.is_panning = False
        
        # Clear all rectangles
        self.ui_manager.canvas.delete("defect")
        
        # Redraw only the selected defect's rectangles
        self._draw_selected_defect_rectangles()
    
    def zoom_in(self):
        """Zoom in on the image"""
        if self.image_processor.zoom_in(*self.ui_manager.get_canvas_dimensions()):
            self.ui_manager.update_image_display(
                self.image_processor.photo_image,
                self.image_processor.current_filename,
                self.image_processor.current_index,
                len(self.image_processor.image_files)
            )
            
            # Redraw only the selected defect's rectangles
            self._draw_selected_defect_rectangles()
    
    def zoom_out(self):
        """Zoom out on the image"""
        if self.image_processor.zoom_out(*self.ui_manager.get_canvas_dimensions()):
            self.ui_manager.update_image_display(
                self.image_processor.photo_image,
                self.image_processor.current_filename,
                self.image_processor.current_index,
                len(self.image_processor.image_files)
            )
            
            # Redraw only the selected defect's rectangles
            self._draw_selected_defect_rectangles()
    
    def reset_zoom(self):
        """Reset zoom to show the entire image"""
        if self.image_processor.reset_zoom(*self.ui_manager.get_canvas_dimensions()):
            self.ui_manager.update_image_display(
                self.image_processor.photo_image,
                self.image_processor.current_filename,
                self.image_processor.current_index,
                len(self.image_processor.image_files)
            )
            
            # Redraw only the selected defect's rectangles
            self._draw_selected_defect_rectangles()
    
    def on_defect_selected(self, index):
        """Handle defect selection"""
        self.logger.debug(f"Defect selected: index={index}")
        
        # First, save the result text from the previously selected defect
        prev_index = self.defect_manager.get_selected_index()
        if prev_index >= 0 and prev_index != index:
            prev_results_text = self.ui_manager.get_result_text()
            self.logger.debug(f"Saving result text from previous defect {prev_index}: '{prev_results_text}'")
            self.defect_manager.update_result_text(prev_index, prev_results_text)
        
        # Check if valid index
        if index < 0:
            self.defect_manager.deselect_defect()
            self.ui_manager.disable_defect_details()
            self.ui_manager.clear_result_text()
            self.ui_manager.clear_rectangles_list()
            self.ui_manager.canvas.delete("defect")
            
            # Add to history after changing selection
            self.add_to_history()
            return False
        
        # Update all UI components based on selection
        defect = self.defect_manager.get_defect(index)
        if not defect:
            return False
            
        self.defect_manager.select_defect(index)
        
        # Clear canvas and redraw only the selected defect rectangles
        self._draw_selected_defect_rectangles()
        
        # Show defect details in form
        self.ui_manager.update_defect_details(
            defect['rename'],
            ""
        )
        
        # Set result text from the defect
        result_text = defect.get("result_text", "")
        self.logger.debug(f"Setting result text for defect {index}: '{result_text}'")
        self.ui_manager.set_result_text(result_text)
        
        # Enable form controls
        self.ui_manager.enable_defect_details()
        
        # Update rectangles list for this defect
        self.ui_manager.update_rectangles_list(index)
        
        # Add to history after changing selection
        self.add_to_history()
        
        return True
    
    def _draw_selected_defect_rectangles(self):
        """Draw only the currently selected defect's rectangles"""
        # First, clear ALL rectangles from the canvas (both defect and drawing tags)
        self.ui_manager.canvas.delete("defect")
        self.ui_manager.canvas.delete("drawing")
        
        # Force canvas to refresh completely
        self.ui_manager.canvas.update_idletasks()
        self.ui_manager.canvas.update()  # Force a more complete update
        
        # Get the selected defect index
        selected_index = self.defect_manager.get_selected_index()
        if selected_index < 0:
            return
            
        defects = self.defect_manager.get_defects()
        if selected_index >= len(defects):
            return
            
        # Get canvas dimensions
        canvas_dimensions = self.ui_manager.get_canvas_dimensions()
        
        # Get the selected defect
        defect = defects[selected_index]
        
        # Draw each rectangle for this defect
        for j, rectangle in enumerate(defect["rectangles"]):
            # Get original coordinates
            image_coords = rectangle["coords"]
            
            # Convert image coordinates to canvas coordinates
            canvas_coords = self.image_processor.image_to_canvas_coords(
                image_coords, canvas_dimensions
            )
            
            if canvas_coords:
                # Unpack coordinates
                canvas_x1, canvas_y1, canvas_x2, canvas_y2 = canvas_coords
                
                # Draw rectangle
                rect_id = self.ui_manager.canvas.create_rectangle(
                    canvas_x1, canvas_y1, canvas_x2, canvas_y2,
                    outline="yellow", fill="yellow", stipple="gray25",
                    tags="defect", width=1
                )
                
                # Update rectangle ID in the defect model
                rectangle["canvas_rect"] = rect_id
        
        # Force canvas to update again after drawing
        self.ui_manager.canvas.update_idletasks()
        self.ui_manager.canvas.update()  # Force a more complete update
        
        # Highlight the selected rectangle if there is one
        rectangle_index = self.defect_manager.get_selected_rectangle_index()
        if rectangle_index >= 0 and rectangle_index < len(defect["rectangles"]):
            rect_id = defect["rectangles"][rectangle_index].get("canvas_rect")
            if rect_id:
                self.ui_manager.canvas.itemconfig(rect_id, outline="red", width=2)
                
        # Final force update
        self.ui_manager.canvas.update_idletasks()
        self.ui_manager.canvas.update()  # Force a more complete update
    
    def on_rectangle_selected(self, rectangle_index):
        """Handle rectangle selection"""
        defect_index = self.defect_manager.get_selected_index()
        if defect_index >= 0 and rectangle_index >= 0:
            self.defect_manager.select_rectangle(rectangle_index)
            self.ui_manager.highlight_rectangle(defect_index, rectangle_index)
    
    def delete_selected_rectangle(self):
        """Delete the selected rectangle"""
        defect_index = self.defect_manager.get_selected_index()
        rectangle_index = self.defect_manager.get_selected_rectangle_index()
        
        if defect_index < 0 or rectangle_index < 0:
            self.ui_manager.show_info("Please select a rectangle to delete.")
            return
        
        # Get the canvas rect ID before deletion
        rectangle = self.defect_manager.get_rectangle(defect_index, rectangle_index)
        if rectangle:
            canvas_rect = rectangle.get("canvas_rect")
            if canvas_rect:
                self.ui_manager.delete_canvas_rect(canvas_rect)
        
        # Remove the rectangle from the defect
        self.defect_manager.remove_rectangle(defect_index, rectangle_index)
        
        # Clear and redraw all rectangles for the current defect
        self.ui_manager.canvas.delete("defect")
        self.ui_manager.canvas.update_idletasks()
        self.ui_manager.canvas.update()
        self._draw_selected_defect_rectangles()
        
        # Update rectangles list
        self.ui_manager.update_rectangles_list(defect_index)
        
        # Add to history
        self.add_to_history()
    
    def delete_defect(self):
        """Delete the selected defect"""
        index = self.defect_manager.get_selected_index()
        if index < 0:
            return
            
        # Get all rectangles in the defect and delete them from the canvas
        rectangles = self.defect_manager.get_rectangles_for_defect(index)
        for rectangle in rectangles:
            canvas_rect = rectangle.get("canvas_rect")
            if canvas_rect:
                self.ui_manager.delete_canvas_rect(canvas_rect)
        
        # Remove defect from the model
        self.defect_manager.remove_defect(index)
        
        # Update UI
        self.ui_manager.remove_defect_from_list(index)
        self.ui_manager.clear_rectangles_list()
        self.ui_manager.disable_defect_details()
        
        # Select another defect if available
        if self.defect_manager.get_defect_count() > 0:
            new_index = min(index, self.defect_manager.get_defect_count() - 1)
            self.ui_manager.select_defect(new_index)
            
        # Add to history
        self.add_to_history()
    
    def on_rename_changed(self, new_name):
        """Handle changes to the rename field"""
        # Update the rename value in the current defect
        current_index = self.defect_manager.get_selected_index()
        if current_index >= 0:
            current_defect = self.defect_manager.get_defect(current_index)
            if current_defect:
                # Get the base filename without extension
                filename_base, _ = self.image_processor.get_current_filename_parts()
                # Get defect number (index + 1)
                defect_number = current_index + 1
                # Update the rename value with proper format
                current_defect["rename"] = f"{filename_base}_{defect_number}:{new_name}"
            
            # Add to history
            self.add_to_history()
    
    def add_to_history(self):
        """Add current state to history"""
        self.history_manager.add_state(self.defect_manager.get_defects_copy())
    
    def _on_window_configure(self, event):
        """Handle window configuration changes"""
        # Only handle if it's the root window being configured
        if event.widget == self.root and hasattr(self, 'ui_manager'):
            # Check if window is in a maximized state
            is_maximized = self.root.state() == 'zoomed'  # 'zoomed' is Windows-specific for maximized
            
            # If maximized, make sure the right panel is visible
            if is_maximized:
                # Use a delay to let the window finish changing size
                self.root.after(100, lambda: self.ui_manager._force_right_panel_visible())
    
    def undo(self):
        """Undo last action"""
        if self.history_manager.can_undo():
            self.history_manager.undo()
            self.restore_state()
            return True
        return False
    
    def redo(self):
        """Redo last undone action"""
        if self.history_manager.can_redo():
            self.history_manager.redo()
            self.restore_state()
    
    def restore_state(self):
        """Restore state from history"""
        state = self.history_manager.get_current_state()
        if state:
            # Save the current selected index
            selected_index = self.defect_manager.get_selected_index()
            
            # Set the new state
            self.defect_manager.set_defects(state)
            
            # Clear the UI
            self.ui_manager.clear_defects_list()
            self.ui_manager.canvas.delete("defect")
            
            # Refresh defects list
            for defect in state:
                self.ui_manager.add_defect_to_list(defect["name"])
                
                # Ensure all defects have valid rename fields
                if not defect.get('rename'):
                    filename, _ = self.image_processor.get_current_filename_parts()
                    index = state.index(defect)
                    defect['rename'] = f"{filename}_{index + 1}"
            
            # Select the same defect if it still exists
            if 0 <= selected_index < len(state):
                self.ui_manager.select_defect(selected_index)
            elif len(state) > 0:
                # Select the first defect if previous selection is no longer valid
                self.ui_manager.select_defect(0)
            else:
                # Clear details if no defects
                self.ui_manager.disable_defect_details()
                self.ui_manager.clear_result_text()
        else:
            # This happens when we've undone to before the first state
            self.defect_manager.clear_defects()
            self.ui_manager.clear_defects_list()
            self.ui_manager.redraw_canvas()
            self.ui_manager.disable_defect_details()
    
    def save_image(self):
        """Save the current image with all active defects"""
        self.logger.info("Saving image with all defects")
        
        # Debug log current state before saving
        current_selected_index = self.defect_manager.get_selected_index()
        self.logger.debug(f"Current selected defect index: {current_selected_index}")
        
        # Ensure we have all required data
        if not self.image_processor.has_current_image() or not self.image_processor.get_current_filename():
            self.logger.error("No image loaded or filename is missing")
            return False
            
        # Save the results from current defect before proceeding
        if current_selected_index >= 0:
            current_results_text = self.ui_manager.get_result_text()
            self.logger.debug(f"Before saving: Updating result text for defect {current_selected_index}: '{current_results_text}'")
            self.defect_manager.update_result_text(current_selected_index, current_results_text)
        
        # Check if any defects are marked
        defects = self.defect_manager.get_defects()
        if not defects:
            self.logger.warning("No defects to save")
            self.ui_manager.update_status("No defects to save")
            return False
        
        # Validate all defects before saving
        for index, defect in enumerate(defects):
            # Skip defects with no rectangles or name
            if not defect.get("rectangles") or len(defect["rectangles"]) == 0:
                self.logger.warning(f"Defect {index} has no rectangles")
                self.ui_manager.show_warning(f"Defect '{defect.get('name')}' has no rectangles. Please draw at least one rectangle.")
                # Select the defect that needs attention
                self.ui_manager.select_defect(index)
                return False
                
            if not defect.get("name"):
                self.logger.warning(f"Skipping defect {index}: No name")
                continue
            
            # Check if there's a custom suffix (indicated by a colon in the rename field)
            has_custom_suffix = False
            if defect and "rename" in defect:
                # Check if there's a colon AND content after the colon
                if ":" in defect["rename"]:
                    suffix = defect["rename"].split(":", 1)[1]
                    has_custom_suffix = bool(suffix.strip())
            
            if not has_custom_suffix:
                self.logger.warning(f"Defect {index} has no custom filename suffix")
                self.ui_manager.show_warning(f"Defect '{defect.get('name')}' has no custom filename suffix. Please add a custom suffix.")
                # Select the defect that needs attention
                self.ui_manager.select_defect(index)
                return False
            
            # Get the result text for this defect
            result_text = defect.get("result_text", "")
            
            # Check if result text is empty
            if not result_text.strip():
                self.logger.warning(f"Defect {index} has empty result text")
                self.ui_manager.show_warning(f"Defect '{defect.get('name')}' has no result text. Please add a result description.")
                # Select the defect that needs attention
                self.ui_manager.select_defect(index)
                return False
        
        # Get the original image (without any drawings)
        original_image = self.image_processor.get_original_image()
        if not original_image:
            self.logger.error("Failed to get original image")
            return False
        
        # Get the current filename
        current_filename = self.image_processor.get_current_filename()
        
        # Save each defect as a separate image
        save_count = 0
        excel_error = None  # Track Excel errors specifically
        
        for index, defect in enumerate(defects):
            self.logger.debug(f"Processing defect {index}: {defect.get('name')}")
            
            # Use file_manager to save the image with defect
            success, error_msg = self.file_manager.save_image_with_defect(
                    original_image, 
                    defect, 
                    current_filename,
                    defect.get("result_text", "")
                )
                
            if success:
                save_count += 1
                self.logger.info(f"Saved defect {index}: {defect.get('name')} as {defect.get('rename')}")
            else:
                self.logger.error(f"Failed to save defect {index}: {defect.get('name')} - {error_msg}")
                # Check if this is an Excel error
                if "open in another program" in error_msg:
                    excel_error = error_msg
                    # Break the loop as we can't continue if Excel is open
                    break
        
        # Check if we had an Excel error
        if excel_error:
            self.logger.error(f"Excel error: {excel_error}")
            self.ui_manager.show_warning(f"Excel Warning: {excel_error}")
            return False
            
        # Update status with save results
        if save_count > 0:
            status_msg = f"Saved {save_count} defect image(s)"
            self.logger.info(status_msg)
            self.ui_manager.update_status(status_msg)
            return True
        else:
            status_msg = "No defects were saved"
            self.logger.warning(status_msg)
            self.ui_manager.update_status(status_msg)
            return False
    
    def save_and_next(self):
        """Save and go to next image"""
        self.logger.info("Starting save_and_next operation")
        
        # Debug logging before save_image
        current_selected_index = self.defect_manager.get_selected_index()
        if current_selected_index >= 0:
            self.logger.debug(f"Before save_image: Selected defect index is {current_selected_index}")
            defect = self.defect_manager.get_defect(current_selected_index)
            if defect:
                self.logger.debug(f"Before save_image: Defect {current_selected_index} has name={defect.get('name')}, "
                                f"rename={defect.get('rename')}, result_text={defect.get('result_text', '')[:30]}...")
        
        # Perform validations for all defects before saving
        defects = self.defect_manager.get_defects()
        for index, defect in enumerate(defects):
            # Save current results text to the defect
            if index == current_selected_index:
                current_results_text = self.ui_manager.get_result_text()
                self.logger.debug(f"Before saving: Updating result text for defect {index}: '{current_results_text}'")
                self.defect_manager.update_result_text(index, current_results_text)
            
            # Get updated result text from the defect
            result_text = self.defect_manager.get_defect_result_text(index)
            self.logger.debug(f"DefectManager: Retrieved result text for defect {index}: '{result_text}'")
            
            # Check for required data in each defect
            if not defect.get("rectangles") or len(defect["rectangles"]) == 0:
                self.logger.warning(f"Defect {index} has no rectangles")
                self.ui_manager.show_warning(f"Defect '{defect.get('name')}' has no rectangles. Please draw at least one rectangle.")
                return
                
            # Check if there's a custom suffix (indicated by a colon in the rename field)
            has_custom_suffix = False
            if defect and "rename" in defect:
                # Check if there's a colon AND content after the colon
                if ":" in defect["rename"]:
                    suffix = defect["rename"].split(":", 1)[1]
                    has_custom_suffix = bool(suffix.strip())
            
            if not has_custom_suffix:
                self.logger.warning(f"Defect {index} has no custom filename suffix")
                self.ui_manager.show_warning(f"Defect '{defect.get('name')}' has no custom filename suffix. Please add a custom suffix.")
                # Select the defect that needs attention
                self.ui_manager.select_defect(index)
                return
                
            # Check if result text is empty
            self.logger.debug(f"Defect {index}: Name={defect.get('name')}, Rename={defect.get('rename')}, Result Text='{result_text}'")
            if not result_text.strip():
                self.logger.warning(f"Defect {index} has empty result text")
                self.ui_manager.show_warning(f"Defect '{defect.get('name')}' has no result text. Please add a result description.")
                # Select the defect that needs attention
                self.ui_manager.select_defect(index)
                return
                
        # All validations passed, proceed with saving
        if self.save_image():
            # Debug logging after save_image
            self.logger.debug(f"After save_image: Current defect count is {self.defect_manager.get_defect_count()}")
            current_selected_index = self.defect_manager.get_selected_index()
            if current_selected_index >= 0:
                self.logger.debug(f"After save_image: Selected defect index is {current_selected_index}")
                defect = self.defect_manager.get_defect(current_selected_index)
                if defect:
                    self.logger.debug(f"After save_image: Defect {current_selected_index} has name={defect.get('name')}, "
                                    f"rename={defect.get('rename')}, result_text={defect.get('result_text', '')[:30]}...")
            
            self.ui_manager.clear_canvas()
            self.next_image()
    
    def next_image(self):
        """Load the next image"""
        self.logger.info("Moving to next image")
        
        # Save the results from current defect before proceeding
        current_selected_index = self.defect_manager.get_selected_index()
        if current_selected_index >= 0:
            current_results_text = self.ui_manager.get_result_text()
            # Use dedicated method for updating result text
            self.logger.debug(f"Before next image: Saving result text from defect {current_selected_index}: '{current_results_text}'")
            self.defect_manager.update_result_text(current_selected_index, current_results_text)
            
            defect = self.defect_manager.get_defect(current_selected_index)
            if defect:
                self.logger.debug(f"After updating results: Defect {current_selected_index} has result_text='{defect.get('result_text', '')[:30]}...'")
        
        next_index = self.image_processor.next_image()
        if next_index is not False:
            self.logger.debug("Loading next image now")
            # Now when we load the next image, always clear the defects
            # This ensures a clean state for each new image
            self.load_image(next_index, preserve_defects=False)
            self.ui_manager.clear_result_text()
    
    def prev_image(self):
        """Load the previous image"""
        self.logger.info("Moving to previous image")
        
        # Save the results from current defect before proceeding
        current_selected_index = self.defect_manager.get_selected_index()
        if current_selected_index >= 0:
            current_results_text = self.ui_manager.get_result_text()
            # Use dedicated method for updating result text
            self.logger.debug(f"Before previous image: Saving result text from defect {current_selected_index}: '{current_results_text}'")
            self.defect_manager.update_result_text(current_selected_index, current_results_text)
        
        prev_index = self.image_processor.prev_image()
        if prev_index is not False:
            self.load_image(prev_index)
            self.ui_manager.clear_result_text()

    def toggle_logging(self, enabled=None):
        """Toggle logging on or off"""
        if enabled is None:
            # Toggle current state
            enabled = not self.logger.enabled
            
        if enabled:
            self.logger.enable()
            self.ui_manager.update_status("Logging enabled")
        else:
            self.logger.disable()
            self.ui_manager.update_status("Logging disabled")
            
    def set_log_level(self, level):
        """Set the logging level"""
        self.logger.set_level(level)
        level_name = "DEBUG" if level == LoggerManager.DEBUG else \
                    "INFO" if level == LoggerManager.INFO else \
                    "WARNING" if level == LoggerManager.WARNING else \
                    "ERROR" if level == LoggerManager.ERROR else \
                    "CRITICAL"
        self.ui_manager.update_status(f"Log level set to {level_name}")

    def no_defects_found(self):
        """Handle 'No Defects Found' button click - move to next image without saving"""
        self.logger.info("No defects found - checking if we can move to next image")
        
        # Check if there are any defects created
        defects = self.defect_manager.get_defects()
        if defects and len(defects) > 0:
            # If defects exist, they must be valid before moving on
            has_rectangles = False
            for defect in defects:
                if defect.get("rectangles") and len(defect["rectangles"]) > 0:
                    has_rectangles = True
                    break
            
            if has_rectangles:
                # If defects with rectangles exist, show warning that they need to be saved first
                self.logger.warning("Cannot skip image - defects with rectangles exist")
                self.ui_manager.show_warning("This image has defects with rectangles. Please either save them or delete them before moving to the next image.")
                return
        
        # No defects with rectangles found, safe to move on
        self.logger.info("Moving to next image without saving")
        self.ui_manager.clear_canvas()
        self.next_image()

    def draw_defect_rectangles(self, defect):
        """Draw all rectangles for a given defect"""
        if not defect or not defect.get("rectangles"):
            self.logger.warning(f"No valid defect or rectangles to draw")
            return 0
            
        # Clear existing rectangles
        self.ui_manager.clear_canvas_elements(["defect", "drawing"])
        
        # Get canvas dimensions
        canvas_dimensions = self.ui_manager.get_canvas_dimensions()
        
        rectangles_drawn = 0
        
        for i, rectangle in enumerate(defect["rectangles"]):
            # Get the image coordinates
            image_coords = rectangle.get("coords")
            if not image_coords or len(image_coords) != 4:
                self.logger.warning(f"Invalid coordinates for rectangle {i}: {image_coords}")
                continue
                
            # Convert image coordinates to canvas coordinates
            canvas_coords = self.image_processor.image_to_canvas_coords(
                image_coords, canvas_dimensions
            )
            
            if canvas_coords:
                # Draw the rectangle on the canvas
                canvas_x1, canvas_y1, canvas_x2, canvas_y2 = canvas_coords
                
                # Create a rectangle on the canvas with a tag for later identification
                rect_id = self.ui_manager.create_rectangle_on_canvas(
                    canvas_x1, canvas_y1, canvas_x2, canvas_y2,
                    outline="yellow", width=2, tags="defect"
                )
                
                # Store the canvas rectangle ID in the defect data
                rectangle["canvas_rect"] = rect_id
                rectangles_drawn += 1
        
        # Force canvas to update again after drawing
        self.ui_manager.update_canvas()
        
        return rectangles_drawn 