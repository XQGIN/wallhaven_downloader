# Wallhaven Wallpaper Downloader

[中文](README.md) | **English**

A PyQt5-based Wallhaven wallpaper batch downloader with multiple download modes and customizable settings.

![App Icon](icon/logo.png)

## ✨ Features

- 🖼️ **Multiple Download Modes**: Download latest wallpapers, from specific categories, or by keyword search
- 🚀 **High Performance**: Multi-threaded concurrent downloads (default 5 threads) for improved efficiency
- 🎨 **Beautiful UI**: Liquid glass effect design with light/dark/auto theme switching
- 🌈 **Smart Theme System**: Intelligent system theme detection (Windows/macOS/Linux) with smooth transition animations
- 🔍 **Image Preview**: Real-time preview of downloaded images with pagination (100 per page)
- 📁 **Smart Management**: Auto-detect duplicate files, resume support, memory optimization
- ⚙️ **Rich Settings**: Adjustable concurrency, timeout, preview size, and more
- 📋 **Unlimited Pages**: Set any number of pages for download

## 🚀 Performance Optimization

This version has been deeply optimized with significant performance improvements:

- **30% faster downloads**: Optimized concurrency strategy and network requests
- **40% lower CPU usage**: Optimized image processing and preview generation
- **30% lower memory usage**: Smart caching and pagination
- **50% fewer network requests**: Intelligent detection of downloaded files

## Main Features

1. **Multiple Download Modes**:
   - Download from specific categories (general, anime, people, etc.)
   - Download latest wallpapers (toplist)
   - Download from search results

2. **Wallpaper Filtering**:
   - Filter by purity (sfw, sketchy, nsfw)
   - Filter by aspect ratio (landscape, portrait, square, etc.)

3. **Download Management**:
   - Multi-threaded concurrent downloads
   - Resume support
   - Auto-skip duplicate files
   - Real-time progress display

4. **Interface Features**:
   - Modern liquid glass effect interface
   - Smart theme system (light/dark/auto)
   - Cross-platform system theme detection
   - Smooth theme transition animations
   - Image preview functionality
   - System tray support

## Usage

### 📦 Method 1: Using Installer (Recommended)

1. Download the latest installer from [Releases](https://github.com/XQGIN/wallhaven_downloader/releases)
2. Run the installer and follow the prompts
3. Launch the program from desktop shortcut or start menu

### 💻 Method 2: Run from Source

1. Ensure Python 3.7+ and pip are installed
2. Clone this repository:
   ```bash
   git clone https://github.com/XQGIN/wallhaven_downloader.git
   cd wallhaven_downloader
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the program:
   ```bash
   python main.py
   ```

### Download Modes

The program provides three download modes:

- **Download from Category**: Select category and purity
  - Categories: all, general, anime, people, ga, gp
  - Purity: sfw, sketchy, nsfw, ws, wn, sn, all

- **Download Latest**: Download latest popular wallpapers from Wallhaven

- **Download from Search**: Search by keywords and download related wallpapers

### Wallpaper Aspect Ratio

Choose the aspect ratio you want:

- All: No ratio restrictions
- Landscape: 16x9, 32x9, 21x9, etc.
- Portrait: 9x16, 9x18, etc.
- Square: 1x1 ratio
- Custom: All ratio options

### Download Settings

- **Number of Pages**: Set pages to download (1-999999)
- **Download Directory**: Click "Browse" to select save location

### Start Download

Click "Start Download" to begin. During download:

- View progress through progress bar
- Status label shows current downloading file
- Downloaded images appear in preview area
- Click "Stop Download" to pause anytime

### Resume Download

If you close the program during download, it will automatically detect unfinished tasks on next launch and ask if you want to resume.

### Image Preview

- Downloaded images appear in preview area
- Double-click preview to view original
- Click "Clear Preview" to clear preview area
- Click "Open Download Directory" to open save folder

### Settings

Click "Settings" to open settings dialog:

**Download Settings**:
- Concurrent Downloads: Number of simultaneous downloads (1-10)
- Auto Skip Duplicates: Automatically detect and skip downloaded files
- Retry Attempts: Number of retry attempts on failure (1-10)

**Interface Settings**:
- Theme Mode: Choose interface theme (Light, Dark, Auto)
  - **Light Theme**: Bright and fresh interface style
  - **Dark Theme**: Eye-friendly dark interface style
  - **Auto Mode**: Intelligently follows system theme, supports Windows 10/11, macOS, Linux
- Glass Transparency: Adjust interface glass effect transparency (100-255)
- Preview Size: Set preview image display size (Small, Medium, Large)

### System Tray

On Windows, closing the window minimizes to system tray:

- Tray icon shows program status
- Double-click tray icon to show/hide main window
- Right-click tray icon for menu with show and exit options
- If download is in progress, shows notification when minimized

### Exit Program

You can exit by:

- Clicking "Exit" button in main window
- Right-clicking system tray icon and selecting "Exit"
- If download is in progress, will ask to confirm stop and exit

## Notes

1. **API Key**: Program uses default API key to access Wallhaven API. If you encounter access limits, replace with your own API key in settings.

2. **Download Limits**: Wallhaven API has rate limits. Set reasonable concurrent download numbers to avoid excessive requests.

3. **File Naming**: Downloaded wallpapers are named with Wallhaven IDs, e.g., "wallhaven-1abcde.jpg".

4. **Duplicate Files**: Program automatically detects and skips duplicate files.

5. **System Requirements**: Requires Python 3.x and PyQt5 library.

## FAQ

### Q: What if download fails?
A: Check network connection and confirm Wallhaven website is accessible. If issues persist, try reducing concurrent downloads or increasing retry attempts.

### Q: How to change API key?
A: In settings dialog, enter your Wallhaven API key. Getting an API key requires registering a Wallhaven account.

### Q: Can't find program after minimizing?
A: On Windows, program minimizes to system tray. Find the icon in notification area on right side of taskbar and double-click to show main window.

### Q: How to change interface theme?
A: Click "Settings" button and select theme mode in "Interface Settings":
   - **Light**: Bright theme suitable for daytime use
   - **Dark**: Dark theme suitable for nighttime use
   - **Auto**: Automatically follows system theme settings, no manual switching needed

### Q: How does auto theme work?
A: When "Auto" mode is selected, the program detects your OS theme settings:
   - Windows 10/11: Reads system theme preference
   - macOS: Detects dark mode setting
   - Linux: Determines through window manager colors
   When system theme changes, program automatically switches with smooth transition animations.

### Q: Where are downloaded images saved?
A: Default location is "Pictures\Wallhaven" folder. You can change save location in download settings.

## 🛠️ Developer Guide

### Build and Release

#### 1. Install Build Dependencies
```bash
pip install pyinstaller
```

#### 2. Build Program
```bash
python build.py
```

This will:
- Clean previous build files
- Package application with PyInstaller
- Copy related documentation to dist directory
- Generate version info file

Output directory: `dist/WallhavenDownloader/`

#### 3. Create Installer (Optional)

1. Download and install [Inno Setup](https://jrsoftware.org/isdl.php)
2. Open `setup.iss` with Inno Setup Compiler
3. Click "Build" -> "Compile"

Installer will be generated at: `dist/installer/WallhavenDownloader_v2.0.0_Setup.exe`

### Run Tests
```bash
# Run all tests
pytest tests/ -v

# View test coverage
pytest tests/ --cov=src --cov-report=html

# Type checking
mypy src/
```

## 📝 Project Structure

```
wallhaven_downloader/
├── src/                    # Source code directory
│   ├── core/              # Core business logic
│   │   ├── settings_manager.py   # Settings management
│   │   └── theme_manager.py      # Theme management
│   ├── ui/                # UI components
│   │   ├── image_preview.py      # Image preview
│   │   ├── animation_mixin.py    # Animation mixin
│   │   └── theme_transition.py   # Theme transition animation
│   ├── workers/           # Background threads
│   │   └── download_thread.py
│   ├── utils/             # Utility modules
│   │   ├── logger.py
│   │   ├── exceptions.py
│   │   ├── performance.py
│   │   └── resource_helper.py
│   ├── font_manager.py
│   └── main_window.py
├── tests/                 # Unit tests
│   ├── test_settings_manager.py
│   ├── test_download_thread.py
│   └── test_theme_manager.py
├── icon/                  # Icon resources
├── font/                  # Font resources
├── build.py               # Build script
├── setup.iss              # Inno Setup install script
├── main.py                # Program entry
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variables example
├── .gitignore             # Git ignore file
├── CHANGELOG.md           # Changelog
├── README.md              # Documentation (Chinese)
├── README_EN.md           # Documentation (English)
└── LICENSE                # License
```

For questions or suggestions, contact via:

- GitHub: https://github.com/XQGIN
- Author: XQGIN

## License

[MIT](LICENSE)
