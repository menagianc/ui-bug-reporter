import copy

class HistoryManager:
    """
    Manager for undo/redo history.
    """
    def __init__(self, max_history=20):
        # History stack
        self.history = []
        self.history_index = -1
        self.max_history = max_history
    
    def add_state(self, state):
        """Add a new state to history"""
        # Make a deep copy to ensure state is preserved
        state_copy = copy.deepcopy(state)
        
        # If we're not at the end of the history, truncate it
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        
        # Add the new state
        self.history.append(state_copy)
        self.history_index = len(self.history) - 1
        
        # Limit history size
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
            self.history_index = len(self.history) - 1
    
    def undo(self):
        """Move back one step in history"""
        if self.history_index >= 0:
            self.history_index -= 1
            return True
        return False
    
    def redo(self):
        """Move forward one step in history"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            return True
        return False
    
    def can_undo(self):
        """Check if undo is possible"""
        return self.history_index > 0
    
    def can_redo(self):
        """Check if redo is possible"""
        return self.history_index < len(self.history) - 1
    
    def get_current_state(self):
        """Get the current state"""
        if 0 <= self.history_index < len(self.history):
            return copy.deepcopy(self.history[self.history_index])
        return None
    
    def clear_history(self):
        """Clear the history"""
        self.history = []
        self.history_index = -1 