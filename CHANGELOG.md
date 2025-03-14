# Change Log

All notable changes to the Image Validator project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.4] - 2024-06-16

### Changed
- Reorganized codebase by moving manager classes into a dedicated 'managers' package
- Created proper Python package structure with __init__.py
- Updated imports to reference the new module structure
- Improved overall code organization for better maintainability

## [1.5.3] - 2024-06-16

### Fixed
- Fixed undo functionality to allow undoing all steps including the first one

## [1.5.2] - 2024-06-16

### Added
- Keyboard shortcuts for Undo (Ctrl+Z) and Redo (Ctrl+Shift+Z)

## [1.5.1] - 2024-06-15

### Fixed
- Fixed image panning functionality to allow proper navigation when zoomed in

## [1.5.0] - 2024-06-15

### Added
- Image zoom functionality with mouse wheel and buttons
- Image panning with middle/right mouse button
- Scrollbars for navigating large images
- Zoom control panel with zoom in/out buttons and reset option
- Navigation help text for zoom and pan operations

### Fixed
- Fixed issue with images appearing too large by implementing proper image resizing
- Improved initial image display to fit within the canvas area

## [1.4.1] - 2024-06-14

### Fixed
- Fixed issue where the right panel with defect details section and controls was not visible

## [1.4.0] - 2024-06-13

### Changed
- Restructured application code from monolithic class to modular architecture
- Separated concerns into specialized manager classes:
  - AppController: Main controller that coordinates all components
  - UIManager: Handles UI components and user interaction
  - ImageProcessor: Manages image loading and processing
  - FileManager: Handles file operations, config, and logging
  - DefectManager: Manages defects and their properties
  - HistoryManager: Provides undo/redo functionality
- Improved code maintainability and readability 
- Enhanced modularity to make future development easier
- Better separation of responsibilities for pinpointing issues

## [1.3.1] - 2024-06-09

### Fixed
- Fixed issue where interacting with defect details fields would deselect the current defect
- Modified save functionality to only save the currently selected defect, not all defects
- Fixed defect persistence issue when navigating between images
- Added safeguard to prevent saving when no defect is selected
- Improved input field behavior in the defect details panel
- Enhanced UI responsiveness when working with defect properties

## [1.3.0] - 2024-06-09

### Changed
- Redesigned from block-based to defect-based approach, where each block represents a defect with its own metadata
- Restructured UI to support defect-specific properties with dedicated details panel
- Updated save functionality to save all defects simultaneously using the same image but different filenames/categories
- Improved CSV log format to include defect-specific information
- Renamed "Blocks" section to "Defects" throughout the application

### Added
- Per-defect renaming capability
- Per-defect categorization
- Defect selection with visual highlighting (red outline)
- Automatic disabling of defect details until a defect is selected

### Removed
- "Save & Reopen" functionality as it's no longer needed (multiple defects can be added to the same image)

## [1.2.0] - 2024-04-18

### Changed
- Modified folder selection behavior to use UI controls instead of initial prompts
- Implemented persistence for folder selections so users are not prompted repeatedly
- Improved overall user experience with more intuitive folder management

## [1.1.0] - 2023-12-19

### Changed
- Renamed application from "Image Validator" to "Bug Validator"
- Changed categories to "Bug for current Project", "Bug for other Project", "No defects found"
- Changed annotations to blocks with yellow color and 35% transparency
- Updated UI layout to include new features
- Modified CSV log format to reflect new block-based approach

### Added
- Undo/redo functionality for block operations
- Two save modes: "Save & Next" and "Save & Reopen"
- Display of current filename in navigation info
- Block naming for easier identification

### Removed
- Text annotations on blocks
- Dedicated annotation input field

## [1.0.0] - 2023-12-18

### Added
- Initial release of the Image Validator
- Core functionality for validating images:
  - Drawing rectangles to mark errors
  - Adding text annotations
  - Categorizing images
  - Renaming images
  - Organizing into category folders
  - Generating CSV logs
- Simple and intuitive user interface
- Support for common image formats

### Rules for Updating This Change Log
1. Always update this file when making changes to the code
2. Use the categories: Added, Changed, Deprecated, Removed, Fixed, Security
3. Include the date of the change
4. Describe the changes in a user-friendly way
5. Keep entries concise but informative 