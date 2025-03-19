import os
import openpyxl
from openpyxl import Workbook

class ExcelManager:
    """
    Manager for all Excel-related operations including creating, updating, and formatting Excel files.
    """
    def __init__(self):
        # Default filename for Excel output
        self.default_excel_filename = "ui_defects.xlsx"
    
    def create_or_load_workbook(self, file_path):
        """Create a new workbook or load an existing one"""
        if os.path.exists(file_path):
            # Load existing workbook
            wb = openpyxl.load_workbook(file_path)
            ws = wb.active
        else:
            # Create a new workbook and set up the headers
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Defect Result"
            ws.append(["Filename", "Title", "Result", "Defect URL"])
        
        return wb, ws
    
    def save_defect_result(self, destination_folder, filename, result_text):
        """
        Save defect result to Excel file
        
        Args:
            destination_folder (str): Path to the destination folder
            filename (str): The filename (with or without extension)
            result_text (str): Result text to save
            
        Returns:
            tuple: (bool, str) - (Success/failure, Error message if any)
        """
        excel_path = os.path.join(destination_folder, self.default_excel_filename)
        
        # Strip the file extension to save only the base filename
        base_filename, _ = os.path.splitext(filename)
        
        try:
            # Get workbook and worksheet
            wb, ws = self.create_or_load_workbook(excel_path)
            
            # Append data to the worksheet
            ws.append([base_filename, "", result_text, ""])
            
            # Save the workbook
            wb.save(excel_path)
            return True, ""
        except PermissionError:
            error_msg = f"Cannot access {self.default_excel_filename} because it is open in another program. Please close Excel and try again."
            print(f"Failed to update Excel file: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Failed to update Excel file: {str(e)}"
            print(error_msg)
            return False, error_msg
    
    def generate_summary_report(self, base_folder):
        """
        Generate a summary report Excel file with statistics
        
        Args:
            base_folder (str): Base folder for the report
            
        Returns:
            str: Path to the generated report file or None if failed
        """
        # This is a placeholder for future functionality
        # You could implement summary statistics across all defects here
        pass
        
    def apply_formatting(self, workbook, worksheet):
        """
        Apply formatting to an Excel worksheet (colors, column widths, etc.)
        
        Args:
            workbook (Workbook): The openpyxl workbook
            worksheet: The worksheet to format
        """
        # This is a placeholder for future formatting functionality
        # For example, you could set column widths, add colors to headers, etc.
        pass 