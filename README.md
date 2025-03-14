# Bug Validator

A simple Python application for validating UI bug screenshots by marking issues with transparent yellow blocks and organizing them into categories.

## Features

- View images one by one
- Draw yellow transparent blocks to mark defects or areas of interest
- Each defect has its own name, category, and rename options
- Multiple defects can be added to a single image
- Select and highlight defects to edit their properties
- Undo/redo defect operations
- Delete selected defects
- Categorize each defect individually (Bug for current Project, Bug for other Project, No defects found)
- Automatically organize defect images into category folders
- Generate a CSV log with detailed records of all validations

## Requirements

- Python 3.6 or higher
- PIL/Pillow library
- openpyxl library

## Installation

1. Clone this repository:
```bash
git clone https://github.com/menagianc/ui-bug-reporter.git
```

2. Create a virtual environment and activate it:

```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:

```bash
python main.py
```
# OR use the batch file on Windows:
```bash
run_bug_validator.bat
```

2. Select the source folder containing images to validate
3. Select the destination folder where validated images will be saved
4. For each image:
   - Draw yellow blocks by clicking and dragging the mouse
   - Select defects from the list to edit their properties
   - Customize the rename field and category for each defect
   - Use Undo/Redo buttons to correct mistakes
   - Click "Save & Next" to save all defects and move to the next image

## Output

- For each defect, a copy of the image with all marked defects is saved
- Images are saved in subfolders according to each defect's category
- Each defect generates a separate file with its own filename
- Yellow transparent blocks are applied to all saved copies
- A CSV file (`validation_log.csv`) is created in the destination folder with details of all validations

## Tips

- The application supports common image formats (.jpg, .jpeg, .png, .bmp, .gif)
- Click on a defect in the defects list to select it and edit its properties
- Selected defects are highlighted with a red outline on the canvas
- Press the "Delete Selected Defect" button to remove a defect
- Use the "Previous" and "Next" buttons to navigate between images
- A minimum rectangle size is required to create a defect
- The undo history stores up to 20 operations

## License

[MIT License](LICENSE) 