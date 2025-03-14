import tkinter as tk
from tkinter import ttk, messagebox

class UIManager:
    """
    Manager for all UI components and interactions.
    """
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        
        # Canvas variables
        self.canvas = None
        self.canvas_frame = None
        self.start_x = 0
        self.start_y = 0
        self.rect_id = None
        
        # UI element references
        self.source_var = tk.StringVar()
        self.dest_var = tk.StringVar()
        self.nav_label = None
        self.defects_listbox = None
        self.rename_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.defect_details_frame = None
        self.rectangles_listbox = None
        self.result_var = tk.StringVar()
        
        # Status bar variables
        self.status_var = tk.StringVar()
        self.status_label = None
        
        # Setup the UI
        self.setup_ui()
        
        # Set up keyboard shortcuts
        self.setup_keyboard_shortcuts()
    
    def setup_ui(self):
        """Set up all UI components"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Bind window state events (maximize, etc.)
        self.root.bind("<Map>", self._on_window_map)
        
        # Create a PanedWindow that will contain the left and right panels
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Left panel (image view)
        left_panel = ttk.Frame(paned_window, relief=tk.SUNKEN, borderwidth=1)
        
        # Right panel (controls)
        right_panel_outer = ttk.Frame(paned_window, width=300)
        # Allow the right panel to resize
        right_panel_outer.pack_propagate(False)
        
        # Add panels to the PanedWindow
        paned_window.add(left_panel, weight=1)  # Give more weight to the left panel (image viewer)
        paned_window.add(right_panel_outer, weight=0)  # Right panel starts with default width
        
        # Store the PanedWindow for later use
        self.paned_window = paned_window
        
        # Set the initial sash position after the window is fully created
        self.root.update_idletasks()
        window_width = self.root.winfo_width()
        paned_window.sashpos(0, window_width - 300)  # Position sash to give right panel 300px
        
        # Store the initial sash proportion
        self._sash_proportion = (window_width - 300) / window_width if window_width > 0 else 0.75
        
        # Force another update and reposition after a short delay to ensure it takes effect
        self.root.after(100, lambda: self._ensure_right_panel_visible())
        
        # Add a canvas and scrollbar for the right panel
        right_panel_canvas = tk.Canvas(right_panel_outer)
        right_scrollbar = ttk.Scrollbar(right_panel_outer, orient=tk.VERTICAL, command=right_panel_canvas.yview)
        right_panel_canvas.configure(yscrollcommand=right_scrollbar.set)
        
        # Pack the scrollbar and canvas
        right_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create a frame inside the canvas to hold all the controls
        right_panel = ttk.Frame(right_panel_canvas)
        
        # Create a window in the canvas for the frame
        canvas_frame_id = right_panel_canvas.create_window((0, 0), window=right_panel, anchor=tk.NW)
        
        # Track mouse position and enable scrolling on hover
        self.enable_right_panel_scroll = False
        
        def _on_right_panel_enter(event):
            self.enable_right_panel_scroll = True
            
        def _on_right_panel_leave(event):
            self.enable_right_panel_scroll = False
        
        # Configure the canvas to scroll with mousewheel when mouse is over the right panel
        def _on_mousewheel(event):
            if self.enable_right_panel_scroll:
                right_panel_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                return "break"  # Prevent event from propagating
        
        # Bind hover events to the right panel elements
        right_panel_outer.bind("<Enter>", _on_right_panel_enter)
        right_panel_outer.bind("<Leave>", _on_right_panel_leave)
        right_panel_canvas.bind("<Enter>", _on_right_panel_enter)
        right_panel_canvas.bind("<Leave>", _on_right_panel_leave)
        right_panel.bind("<Enter>", _on_right_panel_enter)
        right_panel.bind("<Leave>", _on_right_panel_leave)
        right_scrollbar.bind("<Enter>", _on_right_panel_enter)
        right_scrollbar.bind("<Leave>", _on_right_panel_leave)
        
        # Bind the global mousewheel event
        self.root.bind("<MouseWheel>", _on_mousewheel)
        
        # For Linux/Unix systems
        self.root.bind("<Button-4>", self._on_button4)
        self.root.bind("<Button-5>", self._on_button5)
        
        # Update scrollregion when the right panel size changes
        def _configure_right_panel_canvas(event):
            right_panel_canvas.configure(scrollregion=right_panel_canvas.bbox("all"))
            # Also update the width of the canvas window to match the frame width
            right_panel_canvas.itemconfig(canvas_frame_id, width=right_panel_canvas.winfo_width())
        
        right_panel.bind("<Configure>", _configure_right_panel_canvas)
        
        # Store reference to update scroll region after all widgets are added
        self.right_panel = right_panel
        self.right_panel_canvas = right_panel_canvas
        
        # Create a frame for the canvas and scrollbars
        self.canvas_frame = ttk.Frame(left_panel)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add horizontal and vertical scrollbars
        h_scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL)
        v_scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL)
        
        # Create canvas with scrollbars
        self.canvas = tk.Canvas(
            self.canvas_frame,
            bg="lightgray",
            cursor="crosshair",
            xscrollcommand=h_scrollbar.set,
            yscrollcommand=v_scrollbar.set
        )
        
        # Configure scrollbars to scroll the canvas
        h_scrollbar.config(command=self.canvas.xview)
        v_scrollbar.config(command=self.canvas.yview)
        
        # Pack scrollbars and canvas
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Function to provide visual feedback while dragging the sash
        def _on_sash_dragged(event):
            # Update the right panel width based on the current sash position
            current_width = paned_window.winfo_width() - paned_window.sashpos(0)
            right_panel_outer.configure(width=current_width)
            
            # Update just the scroll region during dragging for performance
            # (save full widget scaling for when dragging completes)
            self.right_panel_canvas.configure(width=current_width - 20)
            
            # Update scroll region
            self.right_panel_canvas.configure(scrollregion=self.right_panel_canvas.bbox("all"))
            
            # Update window size in canvas
            for item in self.right_panel_canvas.find_all():
                if self.right_panel_canvas.type(item) == "window":
                    self.right_panel_canvas.itemconfig(item, width=current_width - 20)
        
        # Function to update the right panel when the sash position changes
        def _on_sash_moved(event):
            # Update the right panel width based on the new sash position
            new_width = paned_window.winfo_width() - paned_window.sashpos(0)
            right_panel_outer.configure(width=new_width)
            
            # Update the sash proportion for window resizing
            window_width = self.root.winfo_width()
            if window_width > 0:
                self._sash_proportion = paned_window.sashpos(0) / window_width
            
            # Update the scroll region and scale the widgets
            self._update_right_panel_scroll_region()
            
            # Schedule a delayed update to ensure widget sizes adjust properly after dragging
            self.root.after(50, lambda: self._scale_widgets_to_panel_width(new_width))
        
        # Bind the sash events
        paned_window.bind("<B1-Motion>", _on_sash_dragged)  # During drag
        paned_window.bind("<ButtonRelease-1>", _on_sash_moved)  # After release
        
        # Bind window resize event to update canvas and defects
        self.root.bind("<Configure>", self._on_window_resize)
        
        # Set up canvas event bindings
        self.canvas.bind("<ButtonPress-1>", self.controller.start_draw)
        self.canvas.bind("<B1-Motion>", self.controller.draw)
        self.canvas.bind("<ButtonRelease-1>", self.controller.stop_draw)
        
        # Middle mouse button for panning
        self.canvas.bind("<ButtonPress-2>", self.controller.start_pan)
        self.canvas.bind("<B2-Motion>", self.controller.pan)
        self.canvas.bind("<ButtonRelease-2>", self.controller.stop_pan)
        
        # Mouse wheel for zooming
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        # For Linux/Unix systems
        self.canvas.bind("<Button-4>", lambda e: self.controller.zoom_in())
        self.canvas.bind("<Button-5>", lambda e: self.controller.zoom_out())
        
        # Right mouse button drag for panning as an alternative to middle button
        self.canvas.bind("<ButtonPress-3>", self.controller.start_pan)
        self.canvas.bind("<B3-Motion>", self.controller.pan)
        self.canvas.bind("<ButtonRelease-3>", self.controller.stop_pan)
        
        # Folder selection frame
        folder_frame = ttk.LabelFrame(right_panel, text="Folder Selection")
        folder_frame.pack(fill=tk.X, pady=5)
        
        # Source folder
        source_frame = ttk.Frame(folder_frame)
        source_frame.pack(fill=tk.X, padx=5, pady=2)
        source_label = ttk.Label(source_frame, text="Source:")
        source_label.pack(side=tk.LEFT)
        source_entry = ttk.Entry(source_frame, textvariable=self.source_var, width=15)
        source_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        source_btn = ttk.Button(source_frame, text="Browse", width=8, 
                                command=self.controller.select_source_folder)
        source_btn.pack(side=tk.RIGHT)
        
        # Destination folder
        dest_frame = ttk.Frame(folder_frame)
        dest_frame.pack(fill=tk.X, padx=5, pady=2)
        dest_label = ttk.Label(dest_frame, text="Dest:")
        dest_label.pack(side=tk.LEFT)
        dest_entry = ttk.Entry(dest_frame, textvariable=self.dest_var, width=15)
        dest_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        dest_btn = ttk.Button(dest_frame, text="Browse", width=8,
                              command=self.controller.select_destination_folder)
        dest_btn.pack(side=tk.RIGHT)
        
        # Load images button
        load_btn = ttk.Button(folder_frame, text="Load Images", 
                              command=self.controller.load_images)
        load_btn.pack(fill=tk.X, padx=5, pady=5)
        
        # Zoom controls
        zoom_frame = ttk.LabelFrame(right_panel, text="Zoom")
        zoom_frame.pack(fill=tk.X, pady=5)
        
        zoom_buttons_frame = ttk.Frame(zoom_frame)
        zoom_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        zoom_in_btn = ttk.Button(zoom_buttons_frame, text="+", 
                                command=self.controller.zoom_in, width=3)
        zoom_in_btn.pack(side=tk.LEFT, padx=5)
        
        zoom_out_btn = ttk.Button(zoom_buttons_frame, text="-", 
                                 command=self.controller.zoom_out, width=3)
        zoom_out_btn.pack(side=tk.LEFT, padx=5)
        
        zoom_reset_btn = ttk.Button(zoom_buttons_frame, text="Fit", 
                                   command=self.controller.reset_zoom)
        zoom_reset_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Navigation help text
        nav_help = ttk.Label(zoom_frame, 
                           text="Mouse wheel: Zoom\nRight/middle click: Pan", 
                           justify=tk.LEFT)
        nav_help.pack(fill=tk.X, padx=5, pady=5)
        
        # Navigation info
        nav_frame = ttk.LabelFrame(right_panel, text="Navigation")
        nav_frame.pack(fill=tk.X, pady=5)
        
        self.nav_label = ttk.Label(nav_frame, text="Image 0/0")
        self.nav_label.pack(pady=5)
        
        # Defects list frame
        defects_list_frame = ttk.LabelFrame(right_panel, text="Defects")
        defects_list_frame.pack(fill=tk.X, expand=False, pady=5)
        
        # Defects listbox
        self.defects_listbox = tk.Listbox(defects_list_frame, height=6, exportselection=0)
        self.defects_listbox.pack(fill=tk.X, expand=True, padx=5, pady=5)
        self.defects_listbox.bind('<<ListboxSelect>>', self._on_defect_selected)
        
        # Add defect management buttons
        defect_buttons_frame = ttk.Frame(defects_list_frame)
        defect_buttons_frame.pack(fill=tk.X, padx=5, pady=2)
        
        add_defect_btn = ttk.Button(defect_buttons_frame, text="+", width=3, 
                                 command=self.controller.add_new_defect)
        add_defect_btn.pack(side=tk.LEFT, padx=5)
        
        remove_defect_btn = ttk.Button(defect_buttons_frame, text="-", width=3,
                                    command=self.controller.delete_defect)
        remove_defect_btn.pack(side=tk.LEFT, padx=5)
        
        # Rectangles frame - to display rectangles within selected defect
        rectangles_frame = ttk.LabelFrame(right_panel, text="Rectangles")
        rectangles_frame.pack(fill=tk.X, expand=False, pady=5)
        
        # Rectangles listbox
        self.rectangles_listbox = tk.Listbox(rectangles_frame, height=4, exportselection=0)
        self.rectangles_listbox.pack(fill=tk.X, expand=True, padx=5, pady=5)
        self.rectangles_listbox.bind('<<ListboxSelect>>', self._on_rectangle_selected)
        
        # Add rectangle management buttons
        rectangle_buttons_frame = ttk.Frame(rectangles_frame)
        rectangle_buttons_frame.pack(fill=tk.X, padx=5, pady=2)
        
        remove_rectangle_btn = ttk.Button(rectangle_buttons_frame, text="Delete Rectangle", 
                                       command=self.controller.delete_selected_rectangle)
        remove_rectangle_btn.pack(fill=tk.X, padx=5)
        
        # Defect details frame
        self.defect_details_frame = ttk.LabelFrame(right_panel, text="Defect Details")
        self.defect_details_frame.pack(fill=tk.X, pady=5)
        
        # Rename frame inside defect details
        rename_frame = ttk.Frame(self.defect_details_frame)
        rename_frame.pack(fill=tk.X, padx=5, pady=5)
        rename_label = ttk.Label(rename_frame, text="Rename:")
        rename_label.pack(side=tk.LEFT)
        rename_entry = ttk.Entry(rename_frame, textvariable=self.rename_var)
        rename_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)
        self.rename_var.trace_add("write", self._on_rename_changed)
        
        # Category frame inside defect details
        category_frame = ttk.Frame(self.defect_details_frame)
        category_frame.pack(fill=tk.X, padx=5, pady=5)
        category_label = ttk.Label(category_frame, text="Category:")
        category_label.pack(side=tk.LEFT)
        self.category_var.set(self.controller.file_manager.get_categories()[0])
        category_combo = ttk.Combobox(category_frame, textvariable=self.category_var, 
                                      values=self.controller.file_manager.get_categories(), 
                                      state="readonly")
        category_combo.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)
        self.category_var.trace_add("write", self._on_category_changed)
        
        # Result frame inside defect details
        result_frame = ttk.Frame(self.defect_details_frame)
        result_frame.pack(fill=tk.X, padx=5, pady=5)
        result_label = ttk.Label(result_frame, text="Result:")
        result_label.pack(side=tk.LEFT, anchor=tk.N)
        
        # Result text area with scrollbar
        result_scrollbar = ttk.Scrollbar(result_frame)
        result_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text = tk.Text(result_frame, height=4, width=20, wrap=tk.WORD,
                                  yscrollcommand=result_scrollbar.set)
        self.result_text.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)
        result_scrollbar.config(command=self.result_text.yview)
        
        # Actions frame
        actions_frame = ttk.LabelFrame(right_panel, text="Actions")
        actions_frame.pack(fill=tk.X, pady=5)
        
        undo_btn = ttk.Button(actions_frame, text="Undo", command=self.controller.undo)
        undo_btn.pack(fill=tk.X, padx=5, pady=2)
        
        redo_btn = ttk.Button(actions_frame, text="Redo", command=self.controller.redo)
        redo_btn.pack(fill=tk.X, padx=5, pady=2)
        
        delete_btn = ttk.Button(actions_frame, text="Delete Selected Defect", 
                                command=self.controller.delete_defect)
        delete_btn.pack(fill=tk.X, padx=5, pady=2)
        
        # Save button
        save_frame = ttk.LabelFrame(right_panel, text="Save")
        save_frame.pack(fill=tk.X, pady=5)
        
        save_next_btn = ttk.Button(save_frame, text="Save & Next", 
                                   command=self.controller.save_and_next)
        save_next_btn.pack(fill=tk.X, padx=5, pady=5)
        
        # Navigation buttons
        nav_buttons_frame = ttk.Frame(right_panel)
        nav_buttons_frame.pack(fill=tk.X, pady=10)
        
        prev_btn = ttk.Button(nav_buttons_frame, text="← Previous", 
                              command=self.controller.prev_image)
        prev_btn.pack(side=tk.LEFT, padx=5)
        
        next_btn = ttk.Button(nav_buttons_frame, text="Next →", 
                              command=self.controller.next_image)
        next_btn.pack(side=tk.LEFT, padx=5)
        
        # Initialize defect details as disabled
        self.disable_defect_details()
        
        # Update the scroll region for the right panel after all widgets are added
        self._update_right_panel_scroll_region()
        
        # Add status bar at the bottom of the UI
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Set default status message
        self.status_var.set("Ready")
    
    def _update_right_panel_scroll_region(self):
        """Update the scroll region for the right panel after all widgets are added"""
        self.right_panel.update_idletasks()  # Ensure all widgets are rendered
        self.right_panel_canvas.configure(scrollregion=self.right_panel_canvas.bbox("all"))
        
        # Get the current width of the right panel from the PanedWindow
        right_width = 300  # Default width
        if hasattr(self, 'paned_window'):
            # Calculate width based on paned window's width and sash position
            paned_width = self.paned_window.winfo_width()
            if paned_width > 0:  # Ensure the paned window has been drawn
                sash_pos = self.paned_window.sashpos(0)
                right_width = max(paned_width - sash_pos, 200)  # Ensure minimum width of 200px
                
                # Update the canvas width to match the panel
                self.right_panel_canvas.configure(width=right_width - 20)  # Account for scrollbar and padding
                
                # Update the width of the canvas window to match the frame width
                for item in self.right_panel_canvas.find_all():
                    if self.right_panel_canvas.type(item) == "window":
                        self.right_panel_canvas.itemconfig(item, width=right_width - 20)
                
                # Scale widgets based on right panel width
                self._scale_widgets_to_panel_width(right_width)
        
        # Set minimum height for the right panel to ensure scrollbar works correctly
        min_height = self.right_panel.winfo_reqheight()
        self.right_panel_canvas.configure(height=min(min_height, 800))  # Limit to 800px max height
    
    def _scale_widgets_to_panel_width(self, panel_width):
        """Scale the widgets inside the right panel based on the panel width"""
        # Base scale factor on the panel width
        # Default panel width is 300, so normalize to that
        scale_factor = panel_width / 300.0
        
        # Don't let things get too small or too large
        scale_factor = max(0.8, min(scale_factor, 1.5))
        
        # Recursively update widget sizes in the right panel
        self._update_widget_sizes(self.right_panel, panel_width, scale_factor)
    
    def _update_widget_sizes(self, parent, panel_width, scale_factor):
        """Recursively update widget sizes based on panel width"""
        for widget in parent.winfo_children():
            # Adjust based on widget type
            try:
                # Adjust widget sizes based on type
                if isinstance(widget, ttk.Entry) or isinstance(widget, tk.Entry):
                    # For entries, make them fill more of the available width
                    if "width" in widget.config():
                        current_width = widget.cget("width")
                        if isinstance(current_width, int) and current_width > 0:
                            widget.config(width=max(10, int(current_width * scale_factor)))
                
                elif isinstance(widget, ttk.Button) or isinstance(widget, tk.Button):
                    # Adjust button width if it has a specific width set
                    if "width" in widget.config():
                        current_width = widget.cget("width")
                        if isinstance(current_width, int) and current_width > 0:
                            widget.config(width=max(3, int(current_width * scale_factor)))
                
                elif isinstance(widget, tk.Listbox):
                    # Make listboxes use more of the panel width
                    if "width" in widget.config():
                        widget.config(width=max(15, int(panel_width / 10)))
                
                elif isinstance(widget, tk.Text):
                    # Make text widgets use more of the panel width
                    if "width" in widget.config():
                        widget.config(width=max(15, int(panel_width / 10)))
                
                elif isinstance(widget, ttk.Combobox):
                    # For combobox widgets
                    if "width" in widget.config():
                        current_width = widget.cget("width")
                        if isinstance(current_width, int) and current_width > 0:
                            widget.config(width=max(10, int(current_width * scale_factor)))
                
                # For ttk LabelFrame titles, adjust padding only
                elif isinstance(widget, ttk.LabelFrame):
                    # Adjust internal padding
                    widget.configure(padding=(int(5 * scale_factor)))
                
                # Recursively update children
                if widget.winfo_children():
                    self._update_widget_sizes(widget, panel_width, scale_factor)
                    
            except Exception as e:
                # Skip widgets that don't support these configurations
                pass
    
    def setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts for common operations"""
        # Undo - Ctrl+Z
        self.root.bind('<Control-z>', self._on_undo)
        
        # Redo - Ctrl+Shift+Z
        self.root.bind('<Control-Shift-Z>', self._on_redo)
        # For Windows/Linux systems that might use different case
        self.root.bind('<Control-Shift-z>', self._on_redo)
    
    def _on_undo(self, event=None):
        """Handle undo keyboard shortcut"""
        self.controller.undo()
        return "break"  # Prevent event from propagating
    
    def _on_redo(self, event=None):
        """Handle redo keyboard shortcut"""
        self.controller.redo()
        return "break"  # Prevent event from propagating
    
    def update_folder_paths(self, source, destination):
        """Update the folder path variables in the UI"""
        self.source_var.set(source)
        self.dest_var.set(destination)
    
    def update_source_path(self, path):
        """Update just the source path variable"""
        self.source_var.set(path)
    
    def update_destination_path(self, path):
        """Update just the destination path variable"""
        self.dest_var.set(path)
    
    def update_image_display(self, photo_image, filename, index, total):
        """Update the displayed image and navigation info"""
        # Clear canvas (including all rectangles)
        self.canvas.delete("all")
        
        # Display new image
        if photo_image:
            # Update canvas dimensions
            canvas_width = photo_image.width()
            canvas_height = photo_image.height()
            self.canvas.config(width=canvas_width, height=canvas_height, 
                              scrollregion=(0, 0, canvas_width, canvas_height))
            
            # Display the image
            self.canvas.create_image(0, 0, anchor=tk.NW, image=photo_image)
            
            # Update navigation label
            self.nav_label.config(text=f"Image {index + 1}/{total} - {filename}")
            
            # Redraw only the selected defect's rectangles
            # This ensures that rectangles are always in sync with defect selection
            self.root.after(100, self.controller._draw_selected_defect_rectangles)
    
    def clear_defects_list(self):
        """Clear the defects listbox"""
        self.defects_listbox.delete(0, tk.END)
    
    def add_defect_to_list(self, defect_name):
        """Add a defect to the listbox"""
        self.defects_listbox.insert(tk.END, defect_name)
    
    def remove_defect_from_list(self, index):
        """Remove a defect from the listbox"""
        if 0 <= index < self.defects_listbox.size():
            self.defects_listbox.delete(index)
            
            # Adjust selected item
            if self.defects_listbox.size() > 0:
                new_index = min(index, self.defects_listbox.size() - 1)
                self.defects_listbox.selection_set(new_index)
                self.defects_listbox.see(new_index)
    
    def select_defect(self, index):
        """Select a defect in the listbox"""
        if 0 <= index < self.defects_listbox.size():
            self.defects_listbox.selection_clear(0, tk.END)
            self.defects_listbox.selection_set(index)
            self.defects_listbox.see(index)
            self._on_defect_selected(None)
    
    def start_draw(self, event):
        """Start drawing a rectangle"""
        # Get the canvas coordinates taking into account the scroll position
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="yellow", fill="yellow", stipple="gray25",
            tags="drawing"  # Add tag for identification
        )
    
    def draw(self, event):
        """Continue drawing the rectangle"""
        if self.rect_id:
            # Get the canvas coordinates taking into account the scroll position
            cur_x = self.canvas.canvasx(event.x)
            cur_y = self.canvas.canvasy(event.y)
            self.canvas.coords(self.rect_id, self.start_x, self.start_y, cur_x, cur_y)
    
    def stop_draw(self, event):
        """Finish drawing the rectangle and return the coordinates"""
        if not self.rect_id:
            return None
            
        # Get the canvas coordinates taking into account the scroll position
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
        
        # Ensure rectangle has minimum size
        if abs(end_x - self.start_x) < 5 or abs(end_y - self.start_y) < 5:
            self.canvas.delete(self.rect_id)
            self.rect_id = None
            return None
        
        # Change the rectangle's tag from 'drawing' to 'defect'
        self.canvas.itemconfig(self.rect_id, tags="defect")
        
        # Return canvas coordinates (adjusted for scroll position)
        return (self.start_x, self.start_y, end_x, end_y)
    
    def pan_canvas(self, dx, dy):
        """Pan the canvas by the specified amount"""
        self.canvas.scan_dragto(dx, dy, gain=1)
    
    def start_canvas_scan(self, x, y):
        """Start the canvas scan operation at the given position"""
        self.canvas.scan_mark(x, y)
    
    def continue_canvas_scan(self, x, y):
        """Continue the canvas scan to the new position"""
        self.canvas.scan_dragto(x, y, gain=1)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel events for zooming or scrolling"""
        # If mouse is over the right panel, scroll it
        if self.enable_right_panel_scroll:
            self.right_panel_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            return "break"  # Prevent event from propagating
        # Otherwise, use it for zooming the main canvas
        else:
            # Mouse wheel up = zoom in, down = zoom out
            if event.delta > 0:
                self.controller.zoom_in()
            else:
                self.controller.zoom_out()
    
    def get_canvas_dimensions(self):
        """Get the current canvas dimensions"""
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        # If canvas not yet drawn, use a reasonable default
        if width <= 1 or height <= 1:
            width = 800
            height = 600
            
        return (width, height)
    
    def update_defect_details(self, rename, category):
        """Update the defect detail fields"""
        self.rename_var.set(rename)
        self.category_var.set(category)
        # Don't update results field here as it would overwrite user input
    
    def enable_defect_details(self):
        """Enable the defect detail fields"""
        self._update_defect_details_state(True)
    
    def disable_defect_details(self):
        """Disable the defect detail fields"""
        self._update_defect_details_state(False)
    
    def _update_defect_details_state(self, enabled=False):
        """Update the state of defect detail fields"""
        state = "normal" if enabled else "disabled"
        
        for child in self.defect_details_frame.winfo_children():
            for widget in child.winfo_children():
                if isinstance(widget, (ttk.Entry, ttk.Combobox)):
                    widget.configure(state=state)
                elif isinstance(widget, tk.Text):
                    widget.configure(state=state)
    
    def highlight_defect(self, index):
        """Highlight the selected defect in the listbox"""
        self.defects_listbox.selection_clear(0, tk.END)
        if 0 <= index < self.defects_listbox.size():
            self.defects_listbox.selection_set(index)
            self.defects_listbox.see(index)
            
            # Update rectangles list for this defect
            self.update_rectangles_list(index)
    
    def delete_canvas_rect(self, rect_id):
        """Delete a rectangle from the canvas"""
        if rect_id:
            self.canvas.delete(rect_id)
    
    def clear_canvas(self):
        """Clear the canvas"""
        self.canvas.delete("all")
    
    def redraw_canvas(self):
        """Redraw the canvas with the current image"""
        photo_image = self.controller.image_processor.photo_image
        if photo_image:
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=photo_image)
    
    def redraw_defects(self, defects):
        """Redraw all defects on the canvas"""
        # Clear canvas first
        self.clear_canvas()
        
        # Redisplay the image
        self.redraw_canvas()
        
        # Clear and repopulate listbox
        self.clear_defects_list()
        
        # Get canvas dimensions
        canvas_dimensions = self.get_canvas_dimensions()
        
        # Redraw all defects
        for i, defect in enumerate(defects):
            # Add to listbox
            self.add_defect_to_list(defect["name"])
            
            # We don't draw rectangles here anymore - that's handled by the controller
        
        # Highlight selected defect in the listbox
        defect_index = self.controller.defect_manager.get_selected_index()
        if defect_index >= 0:
            self.highlight_defect(defect_index)
    
    def _on_defect_selected(self, event):
        """Handle defect selection in listbox"""
        selected = self.defects_listbox.curselection()
        if selected:
            index = selected[0]
            self.controller.on_defect_selected(index)
        else:
            self.controller.on_defect_selected(-1)
    
    def _on_rename_changed(self, *args):
        """Handle changes to the rename field"""
        self.controller.on_rename_changed(self.rename_var.get())
    
    def _on_category_changed(self, *args):
        """Handle changes to the category field"""
        self.controller.on_category_changed(self.category_var.get())
    
    def get_result_text(self):
        """Get the contents of the result text field"""
        if hasattr(self, 'result_text'):
            return self.result_text.get("1.0", tk.END).strip()
        return ""
    
    def clear_result_text(self):
        """Clear the contents of the result text field"""
        if hasattr(self, 'result_text'):
            self.result_text.delete("1.0", tk.END)
            
    def set_result_text(self, text):
        """Set the contents of the result text field"""
        if hasattr(self, 'result_text'):
            self.result_text.delete("1.0", tk.END)
            
            self.result_text.insert("1.0", text)
    
    def show_info(self, message):
        """Show an info message"""
        messagebox.showinfo("Info", message)
    
    def show_warning(self, message):
        """Show a warning message"""
        messagebox.showwarning("Warning", message)
    
    def show_error(self, message):
        """Show an error message"""
        messagebox.showerror("Error", message)
    
    def update_status(self, message, clear_after=5000):
        """Update status bar with a message, optionally clear after a delay"""
        self.status_var.set(message)
        
        # Clear status after delay (milliseconds) if specified
        if clear_after:
            self.root.after(clear_after, lambda: self.clear_status())
            
    def clear_status(self):
        """Clear the status bar"""
        self.status_var.set("Ready")
    
    def _on_window_resize(self, event):
        """Handle window resize events"""
        # Only handle if it's the root window being resized
        if event.widget == self.root:
            # Store the current size to check if it actually changed
            if not hasattr(self, '_last_window_size'):
                self._last_window_size = (self.root.winfo_width(), self.root.winfo_height())
                self._sash_proportion = None  # Store the sash proportion
            
            # Get the new size
            new_size = (self.root.winfo_width(), self.root.winfo_height())
            
            # Only proceed if the size actually changed
            if new_size != self._last_window_size:
                old_width = self._last_window_size[0]
                new_width = new_size[0]
                
                # Store the new size
                self._last_window_size = new_size
                
                # Detect if this is a maximize operation (significant size increase)
                is_maximize = (new_width > old_width * 1.5) and (new_width > 1000)
                
                # If we have a PanedWindow, maintain the sash position proportion
                if hasattr(self, 'paned_window') and self.paned_window.winfo_exists():
                    # Calculate the sash proportion if we don't have it yet
                    if self._sash_proportion is None and old_width > 0:
                        current_sash_pos = self.paned_window.sashpos(0)
                        self._sash_proportion = current_sash_pos / old_width
                    
                    # For maximize operation, ensure right panel is always visible
                    if is_maximize:
                        # Force right panel to have a minimum width of 300px
                        new_sash_pos = new_width - 300
                        self.paned_window.sashpos(0, new_sash_pos)
                        # Update the proportion after setting the position
                        self._sash_proportion = new_sash_pos / new_width if new_width > 0 else 0.75
                    # Normal resize, maintain proportion
                    elif self._sash_proportion is not None and 0 <= self._sash_proportion <= 1:
                        new_sash_pos = int(self._sash_proportion * new_width)
                        # Ensure the right panel is at least 200px and at most 50% of the window
                        right_panel_min_width = 200
                        right_panel_max_width = new_width // 2
                        right_panel_width = new_width - new_sash_pos
                        
                        if right_panel_width < right_panel_min_width:
                            new_sash_pos = new_width - right_panel_min_width
                        elif right_panel_width > right_panel_max_width:
                            new_sash_pos = new_width - right_panel_max_width
                        
                        self.paned_window.sashpos(0, new_sash_pos)
                
                # Update the right panel scroll region
                self._update_right_panel_scroll_region()
                
                # Only redraw image if we have a loaded image
                if self.controller.image_processor.has_current_image():
                    # Add a small delay to avoid too many redraws during resize
                    self.root.after_cancel(self._resize_job) if hasattr(self, '_resize_job') else None
                    self._resize_job = self.root.after(100, self._resize_complete)
                    
                # For maximize operations, make an extra attempt to ensure right panel is visible
                if is_maximize:
                    self.root.after(200, self._force_right_panel_visible)

    def _resize_complete(self):
        """Called when resizing is complete to update the image and defects"""
        # Get new canvas dimensions
        canvas_dimensions = self.get_canvas_dimensions()
        
        # Resize the image to fit the new canvas size
        if self.controller.image_processor.resize_image(*canvas_dimensions):
            # Update the image display
            self.update_image_display(
                self.controller.image_processor.photo_image,
                self.controller.image_processor.current_filename,
                self.controller.image_processor.current_index,
                len(self.controller.image_processor.image_files)
            )
            
            # Redraw defects with correct positioning
            self.redraw_defects(self.controller.defect_manager.get_defects()) 
        
        # Update the right panel scroll region
        self._update_right_panel_scroll_region()
    
    def update_rectangles_list(self, defect_index):
        """Update the rectangles listbox based on the selected defect"""
        self.rectangles_listbox.delete(0, tk.END)
        
        if defect_index >= 0:
            rectangles = self.controller.defect_manager.get_rectangles_for_defect(defect_index)
            for i, rectangle in enumerate(rectangles):
                self.rectangles_listbox.insert(tk.END, f"Rectangle {i+1}")
            
            # Select the current rectangle if there is one
            rectangle_index = self.controller.defect_manager.get_selected_rectangle_index()
            if rectangle_index >= 0 and rectangle_index < len(rectangles):
                self.rectangles_listbox.selection_set(rectangle_index)
                self.rectangles_listbox.see(rectangle_index)
                
    def _on_rectangle_selected(self, event):
        """Handle rectangle selection in listbox"""
        selected = self.rectangles_listbox.curselection()
        if selected:
            rectangle_index = selected[0]
            self.controller.on_rectangle_selected(rectangle_index)
    
    def highlight_rectangle(self, defect_index, rectangle_index):
        """Highlight the selected rectangle on the canvas"""
        defects = self.controller.defect_manager.get_defects()
        
        # Reset all rectangles of the selected defect to normal appearance
        if 0 <= defect_index < len(defects):
            for rectangle in defects[defect_index]["rectangles"]:
                rect_id = rectangle.get("canvas_rect")
                if rect_id:
                    self.canvas.itemconfig(rect_id, outline="yellow", width=1)
        
        # Highlight the selected rectangle
        if 0 <= defect_index < len(defects) and 0 <= rectangle_index < len(defects[defect_index]["rectangles"]):
            rect_id = defects[defect_index]["rectangles"][rectangle_index].get("canvas_rect")
            if rect_id:
                self.canvas.itemconfig(rect_id, outline="red", width=2)
    
    def clear_rectangles_list(self):
        """Clear the rectangles list"""
        if self.rectangles_listbox:
            self.rectangles_listbox.delete(0, tk.END)

    def redraw_only_selected_defect(self):
        """Redraw only the selected defect (unused function)"""
        # This function is not called anywhere in the codebase
        defect_index = self.controller.defect_manager.get_selected_index()
        if defect_index >= 0:
            defect = self.controller.defect_manager.get_defect(defect_index)
            self.redraw_defects([defect]) 

    def _on_button4(self, event):
        """Handle Button-4 events (mouse wheel up on Linux/Unix)"""
        if self.enable_right_panel_scroll:
            self.right_panel_canvas.yview_scroll(-1, "units")
            return "break"
        else:
            self.controller.zoom_in()
    
    def _on_button5(self, event):
        """Handle Button-5 events (mouse wheel down on Linux/Unix)"""
        if self.enable_right_panel_scroll:
            self.right_panel_canvas.yview_scroll(1, "units")
            return "break"
        else:
            self.controller.zoom_out()

    def _ensure_right_panel_visible(self):
        """Ensure the right panel is visible with proper width"""
        # Make sure the paned window exists
        if not hasattr(self, 'paned_window') or not self.paned_window.winfo_exists():
            return
            
        # Get the current window width
        window_width = self.root.winfo_width()
        if window_width <= 1:  # Not properly initialized yet
            self.root.after(200, self._ensure_right_panel_visible)
            return
            
        # Calculate the right panel width (at least 300px)
        right_panel_width = 300
        
        # Set the sash position to ensure the right panel has the desired width
        new_sash_pos = max(0, window_width - right_panel_width)
        self.paned_window.sashpos(0, new_sash_pos)
        
        # Update variables tracking sash position
        self._sash_proportion = new_sash_pos / window_width if window_width > 0 else 0.75
        
        # Update the scroll region
        self._update_right_panel_scroll_region()
        
        # Schedule the function to run again after a short delay (run just a few times at startup)
        if not hasattr(self, '_ensure_attempts'):
            self._ensure_attempts = 1
        else:
            self._ensure_attempts += 1
            
        # Only continue attempting during initial startup (5 attempts max)
        if self._ensure_attempts < 5:
            self.root.after(200, self._ensure_right_panel_visible)
            
    def _force_right_panel_visible(self):
        """Force right panel to be visible after maximize operations"""
        # Make sure the paned window exists
        if not hasattr(self, 'paned_window') or not self.paned_window.winfo_exists():
            return
            
        # Get the current window width
        window_width = self.root.winfo_width()
        if window_width <= 1:  # Not properly initialized yet
            return
            
        # Set the sash position to give right panel exactly 300px
        new_sash_pos = window_width - 300
        self.paned_window.sashpos(0, new_sash_pos)
        
        # Update the scroll region
        self._update_right_panel_scroll_region()
    
    def _on_window_map(self, event):
        """Handle window map events (including maximize/restore)"""
        # Check if the window is mapped (visible) and ensure right panel is visible
        if event.widget == self.root:
            # Use a short delay to allow the window to be fully mapped
            self.root.after(100, self._force_right_panel_visible) 