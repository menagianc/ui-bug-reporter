import tkinter as tk
from managers.ui_manager import UIManager
from managers.image_processor import ImageProcessor
from managers.file_manager import FileManager
from managers.defect_manager import DefectManager
from managers.history_manager import HistoryManager

class AppController:
    """
    Main controller class that coordinates all components of the application.
    """
    def __init__(self, root):
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
    
    def load_image(self, index):
        """Load and display a specific image"""
        if not self.image_processor.load_image(index):
            return False
            
        # Reset states
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
            rename=f"{filename}_{defect_name}",
            category=self.file_manager.get_categories()[0]
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
        
        # Save current results text to the current defect
        current_selected_index = self.defect_manager.get_selected_index()
        if current_selected_index >= 0:
            current_results_text = self.ui_manager.get_result_text()
            current_defect = self.defect_manager.get_defect(current_selected_index)
            if current_defect:
                current_defect["result_text"] = current_results_text
        
        # Clear ALL rectangles from canvas (both defect and drawing tags)
        self.ui_manager.canvas.delete("defect")
        self.ui_manager.canvas.delete("drawing")
        
        # Force canvas to refresh completely
        self.ui_manager.canvas.update_idletasks()
        self.ui_manager.canvas.update()  # Force a more complete update
        
        # Create new defect name
        defect_name = f"Defect {self.defect_manager.get_defect_count() + 1}"
        filename, _ = self.image_processor.get_current_filename_parts()
        
        # Add a new defect with no rectangles yet
        defect = self.defect_manager.add_defect(
            name=defect_name,
            rename=f"{filename}_{defect_name}",
            category=self.file_manager.get_categories()[0]
        )
        
        # Clear results text for the new defect
        self.ui_manager.clear_result_text()
        
        # Update UI
        self.ui_manager.add_defect_to_list(defect_name)
        self.ui_manager.select_defect(self.defect_manager.get_defect_count() - 1)
        
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
        # Save current results text to the current defect before switching
        current_selected_index = self.defect_manager.get_selected_index()
        if current_selected_index >= 0:
            current_results_text = self.ui_manager.get_result_text()
            current_defect = self.defect_manager.get_defect(current_selected_index)
            if current_defect:
                current_defect["result_text"] = current_results_text
        
        # First deselect the current defect and clear ALL rectangles
        self.defect_manager.deselect_defect()
        
        # Clear ALL rectangles from the canvas before doing anything else (both defect and drawing tags)
        self.ui_manager.canvas.delete("defect")
        self.ui_manager.canvas.delete("drawing")
        
        # Force canvas to refresh completely
        self.ui_manager.canvas.update_idletasks()
        self.ui_manager.canvas.update()  # Force a more complete update
        
        if 0 <= index < self.defect_manager.get_defect_count():
            # Now select the new defect
            self.defect_manager.select_defect(index)
            defect = self.defect_manager.get_selected_defect()
            
            # Update UI details
            self.ui_manager.update_defect_details(
                defect['rename'],
                defect['category']
            )
            self.ui_manager.enable_defect_details()
            
            # Load results text for this defect
            self.ui_manager.clear_result_text()
            if "result_text" in defect and defect["result_text"]:
                self.ui_manager.set_result_text(defect["result_text"])
            
            # Update rectangles list
            self.ui_manager.update_rectangles_list(index)
            
            # Draw ONLY the selected defect's rectangles
            self._draw_selected_defect_rectangles()
            
            # Highlight the defect in the listbox
            self.ui_manager.highlight_defect(index)
        else:
            # If no defect selected, just clear everything
            self.ui_manager.disable_defect_details()
            self.ui_manager.clear_rectangles_list()
            self.ui_manager.clear_result_text()
    
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
        """Update defect rename property"""
        self.defect_manager.update_selected_defect_property('rename', new_name)
    
    def on_category_changed(self, new_category):
        """Update defect category property"""
        self.defect_manager.update_selected_defect_property('category', new_category)
    
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
        """Save the current image with all defects"""
        if not self.image_processor.has_current_image():
            self.ui_manager.show_info("No image to save.")
            return False
        
        if not self.file_manager.check_folders():
            self.ui_manager.show_warning("Source and destination folders must be selected.")
            return False
        
        if self.defect_manager.get_defect_count() == 0:
            self.ui_manager.show_warning("No defects marked. Add at least one defect before saving.")
            return False
        
        # Save current results text to the current defect
        current_selected_index = self.defect_manager.get_selected_index()
        if current_selected_index >= 0:
            current_results_text = self.ui_manager.get_result_text()
            current_defect = self.defect_manager.get_defect(current_selected_index)
            if current_defect:
                current_defect["result_text"] = current_results_text
                print(f"Saved result text for defect {current_defect['name']}")
        
        # Get all defects
        defects = self.defect_manager.get_defects()
        print(f"Total defects count: {len(defects)}")
        
        # Process and save image for each defect
        current_image = self.image_processor.get_original_image()
        current_filename = self.image_processor.get_current_filename()
        
        save_success = True
        defects_saved = 0
        for i, defect in enumerate(defects):
            print(f"Processing defect {i+1}: {defect['name']}, rectangles: {len(defect['rectangles'])}")
            # Only save defects that have at least one rectangle
            if len(defect["rectangles"]) > 0:
                # Use each defect's individual result text
                defect_result_text = defect.get("result_text", "")
                success = self.file_manager.save_image_with_defect(
                    original_image=current_image,
                    defect=defect,
                    original_filename=current_filename,
                    result_text=defect_result_text
                )
                if success:
                    defects_saved += 1
                save_success = save_success and success
            else:
                print(f"Skipping defect {defect['name']} because it has no rectangles")
        
        if save_success:
            # Use status bar instead of message box for successful saves
            self.ui_manager.update_status(f"All defects saved successfully. Total: {defects_saved}")
        else:
            # Still show warning for failures
            self.ui_manager.show_warning(f"Some defects could not be saved. Saved: {defects_saved}/{len(defects)}")
            
        return save_success
    
    def save_and_next(self):
        """Save and go to next image"""
        if self.save_image():
            self.ui_manager.clear_canvas()
            self.ui_manager.clear_result_text()
            self.next_image()
    
    def next_image(self):
        """Load next image"""
        current = self.image_processor.current_index
        if current < len(self.image_processor.image_files) - 1:
            self.load_image(current + 1)
        else:
            # Use status bar instead of message box
            self.ui_manager.update_status("This is the last image.")
    
    def prev_image(self):
        """Load previous image"""
        current = self.image_processor.current_index
        if current > 0:
            self.load_image(current - 1)
        else:
            # Use status bar instead of message box
            self.ui_manager.update_status("This is the first image.") 