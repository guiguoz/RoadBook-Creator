# Roadbook Editor

A professional roadbook editor application for orienteering and multi-sport raids.

## Features

- Create and manage vignettes with distances and diagrams
- Graphical editor with drawing tools (arrows, markers, text)
- Professional PDF export with adaptive layout
- SVG-based diagram storage
- Undo/redo functionality in the editor
- Intuitive PyQt5 user interface

## Installation

1. Ensure Python 3.7+ is installed
2. Run the installation script:
   ```
   launch.bat
   ```

## Usage

1. Launch the application using `launch.bat`
2. Add vignettes using the "Ajouter Vignette" button
3. Double-click on the diagram column to edit schemas
4. Use the drawing tools to create navigation diagrams
5. Export to PDF using the "Exporter en PDF" button

## Architecture

- `main.py`: Main application interface
- `vignette_editor.py`: Graphical diagram editor
- `pdf_exporter.py`: PDF export functionality
- `vignette_model.py`: Data model for vignettes
- `widgets.py`: Custom UI widgets
- `logging_config.py`: Centralized logging configuration

## Security Improvements

- Path traversal protection in file operations
- Proper error handling with logging
- Input validation and sanitization
- Resource management for graphics operations

## Performance Optimizations

- Efficient SVG rendering with caching
- Optimized mouse event handling
- Memory-conscious undo/redo implementation
- Reduced code duplication

## Logging

Application logs are stored in the `logs/` directory with daily rotation.
Log levels can be configured in `logging_config.py`.

## Requirements

See `requirements.txt` for Python dependencies.