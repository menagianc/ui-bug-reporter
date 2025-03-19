import tkinter as tk
from tkinter import messagebox

class UIManager:
    def show_error(self, message):
        """Show an error dialog with the given message"""
        messagebox.showerror("Error", message)
        
    def show_warning(self, message):
        """Show a warning dialog with the given message"""
        messagebox.showwarning("Warning", message)
        
    def show_info(self, message):
        """Show an info dialog with the given message"""
        messagebox.showinfo("Information", message) 