# Project Structure

## Architecture Overview

The project follows a modular architecture with clear separation of concerns:

```
wallhaven_downloader/          # Main package
├── core/                      # Business logic & configuration
├── ui/                        # User interface components
├── utils/                     # Utilities & helpers
├── workers/                   # Background threads
├── controllers/               # MVC controllers (empty)
├── viewmodels/               # MVVM view models (empty)
├── main_window.py            # Main application window
├── font_manager.py           # Font management
└── __main__.py               # Briefcase entry point
```

## Module Organization

### Core (`wallhaven_downloader/core/`)
- **Business Logic**: Settings, themes, i18n, configuration
- **Key Files**: 
  - `settings_manager.py`: Application settings
  - `theme_manager.py`: Theme system
  - `i18n_manager.py`: Internationalization
  - `apple_color_palette.py`: Apple-style colors

### UI (`wallhaven_downloader/ui/`)
- **Components**: Glass effects, animations, layouts
- **Patterns**: 
  - Glass components: `glass_*.py` files
  - Enhanced inputs: `enhanced_*.py` files
  - Animation system: `animation/` subfolder
  - Liquid glass effects: `liquid_glass/` subfolder

### Utils (`wallhaven_downloader/utils/`)
- **Utilities**: Logging, performance, accessibility, resources
- **Key Components**:
  - `logger.py`: Centralized logging
  - `performance_optimizer.py`: Performance management
  - `accessibility_manager.py`: A11y support
  - `resource_helper.py`: Resource path resolution

### Workers (`wallhaven_downloader/workers/`)
- **Background Tasks**: Download threads, async operations
- **Pattern**: Thread-based workers for non-blocking operations

## Coding Conventions

### Import Patterns
```python
# Try local import first, fallback to package import
try:
    from utils.logger import get_logger
except ImportError:
    from wallhaven_downloader.utils.logger import get_logger
```

### Resource Management
```python
# Use resource_path() for all file resources
def resource_path(relative_path):
    """Handle both development and packaged environments"""
    try:
        base_path = sys._MEIPASS  # PyInstaller
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(base_path, relative_path)
```

### UI Component Structure
- Glass components inherit from base Qt widgets
- Use manager classes for complex functionality
- Implement accessibility features in all interactive components
- Follow Apple design language for visual consistency

### Configuration Management
- Settings stored in `settings.json` (runtime)
- Environment variables in `.env` file
- Localization files in `locales/` directory
- Resource files (icons, fonts) in dedicated folders

## File Naming Conventions
- **Glass UI**: `glass_*.py` for glass effect components
- **Enhanced UI**: `enhanced_*.py` for improved standard components  
- **Managers**: `*_manager.py` for singleton management classes
- **Threads**: `*_thread.py` for worker threads
- **Utils**: Descriptive names in `utils/` folder

## Entry Points
- **Development**: `main.py` (PyInstaller compatible)
- **Briefcase**: `wallhaven_downloader/__main__.py`
- **Package**: `wallhaven_downloader/__init__.py`