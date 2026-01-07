# Technology Stack

## Core Framework
- **PyQt5 5.15.9**: Main GUI framework
- **Python 3.7+**: Programming language
- **Requests 2.31.0**: HTTP client for API calls
- **Pillow**: Image processing and manipulation
- **psutil**: System and process utilities

## Key Libraries
- **loguru**: Advanced logging system
- **python-dotenv**: Environment configuration
- **urllib3**: HTTP client utilities

## Build Systems

### Primary: Briefcase (Cross-platform)
```bash
# Install Briefcase
pip install briefcase>=0.3.18

# Quick build (automated)
python build_briefcase.py

# Manual build steps
briefcase create   # Create app structure
briefcase build    # Build application
briefcase package  # Create installer

# Development
briefcase dev      # Run in dev mode
briefcase run      # Run packaged app
```

### Secondary: PyInstaller (Windows focused)
```bash
# Build executable
python build.py

# Test executable
dist\WallhavenDownloader\WallhavenDownloader.exe

# Create installer (requires Inno Setup)
# Compile setup.iss with Inno Setup Compiler
```

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python main.py

# Run tests
pytest tests/ -v
pytest tests/ --cov=src --cov-report=html

# Type checking
mypy src/

# Clean build artifacts
# Handled automatically by build scripts
```

## Configuration Files
- `pyproject.toml`: Briefcase configuration
- `requirements.txt`: Python dependencies
- `setup.iss`: Inno Setup installer script
- `.env.example`: Environment variables template
- `settings.json`: Application settings (runtime)

## Platform-Specific Notes
- **Windows**: Uses Acrylic/Mica effects for glass UI
- **macOS**: Uses NSVisualEffectView for native blur
- **Linux**: Uses QGraphicsBlurEffect fallback