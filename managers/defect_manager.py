import copy

class DefectManager:
    """
    Manager for defects (bugs/issues) marked on images.
    """
    def __init__(self):
        # Defects list
        self.defects = []
        
        # Selected defect index
        self.selected_index = -1
        
        # Selected rectangle index within the defect
        self.selected_rectangle_index = -1
    
    def add_defect(self, name, rename, category):
        """Add a new defect instance with no rectangles yet"""
        defect = {
            "name": name,
            "rename": rename,
            "category": category,
            "rectangles": [],  # List to hold multiple rectangles
            "result_text": ""  # Add result text field for each defect
        }
        
        self.defects.append(defect)
        return defect
    
    def add_rectangle_to_defect(self, defect_index, coords, canvas_rect=None):
        """Add a rectangle to an existing defect"""
        if 0 <= defect_index < len(self.defects):
            rectangle = {
                "coords": coords,
                "canvas_rect": canvas_rect
            }
            self.defects[defect_index]["rectangles"].append(rectangle)
            return True
        return False
    
    def get_rectangle(self, defect_index, rectangle_index):
        """Get a specific rectangle from a defect"""
        if 0 <= defect_index < len(self.defects) and 0 <= rectangle_index < len(self.defects[defect_index]["rectangles"]):
            return self.defects[defect_index]["rectangles"][rectangle_index]
        return None
    
    def get_rectangles_for_defect(self, defect_index):
        """Get all rectangles for a specific defect"""
        if 0 <= defect_index < len(self.defects):
            return self.defects[defect_index]["rectangles"]
        return []
    
    def get_rectangle_count_for_defect(self, defect_index):
        """Get the number of rectangles for a specific defect"""
        if 0 <= defect_index < len(self.defects):
            return len(self.defects[defect_index]["rectangles"])
        return 0
    
    def remove_rectangle(self, defect_index, rectangle_index):
        """Remove a rectangle from a defect"""
        if 0 <= defect_index < len(self.defects) and 0 <= rectangle_index < len(self.defects[defect_index]["rectangles"]):
            # Remove the rectangle
            del self.defects[defect_index]["rectangles"][rectangle_index]
            
            # Update selected rectangle index
            if self.selected_rectangle_index == rectangle_index:
                self.selected_rectangle_index = -1
            elif self.selected_rectangle_index > rectangle_index:
                self.selected_rectangle_index -= 1
            
            return True
        return False
    
    def get_defect(self, index):
        """Get a specific defect by index"""
        if 0 <= index < len(self.defects):
            return self.defects[index]
        return None
    
    def get_defects(self):
        """Get all defects"""
        return self.defects
    
    def get_defects_copy(self):
        """Get a deep copy of all defects for history management"""
        return copy.deepcopy(self.defects)
    
    def set_defects(self, defects):
        """Replace all defects with a new set"""
        self.defects = defects
        self.selected_index = -1
        self.selected_rectangle_index = -1
    
    def get_defect_count(self):
        """Get the number of defects"""
        return len(self.defects)
    
    def remove_defect(self, index):
        """Remove a defect by index"""
        if 0 <= index < len(self.defects):
            # Remove the defect
            del self.defects[index]
            
            # Update selected index
            if self.selected_index == index:
                self.selected_index = -1
                self.selected_rectangle_index = -1
            elif self.selected_index > index:
                self.selected_index -= 1
    
    def clear_defects(self):
        """Remove all defects"""
        self.defects = []
        self.selected_index = -1
        self.selected_rectangle_index = -1
    
    def select_defect(self, index):
        """Select a defect by index"""
        if 0 <= index < len(self.defects):
            self.selected_index = index
            # Reset rectangle selection when selecting a new defect
            self.selected_rectangle_index = -1 if len(self.defects[index]["rectangles"]) == 0 else 0
    
    def select_rectangle(self, rectangle_index):
        """Select a specific rectangle within the selected defect"""
        if self.selected_index >= 0 and 0 <= rectangle_index < len(self.defects[self.selected_index]["rectangles"]):
            self.selected_rectangle_index = rectangle_index
            return True
        return False
    
    def deselect_defect(self):
        """Clear defect selection"""
        self.selected_index = -1
        self.selected_rectangle_index = -1
    
    def get_selected_index(self):
        """Get the index of the selected defect"""
        return self.selected_index
    
    def get_selected_rectangle_index(self):
        """Get the index of the selected rectangle"""
        return self.selected_rectangle_index
    
    def get_selected_defect(self):
        """Get the selected defect"""
        if self.selected_index >= 0 and self.selected_index < len(self.defects):
            return self.defects[self.selected_index]
        return None
    
    def get_selected_rectangle(self):
        """Get the selected rectangle within the selected defect"""
        defect = self.get_selected_defect()
        if defect and self.selected_rectangle_index >= 0 and self.selected_rectangle_index < len(defect["rectangles"]):
            return defect["rectangles"][self.selected_rectangle_index]
        return None
    
    def update_selected_defect_property(self, property_name, value):
        """Update a property of the selected defect"""
        if self.selected_index >= 0 and property_name:
            defect = self.defects[self.selected_index]
            defect[property_name] = value
            return True
        return False 