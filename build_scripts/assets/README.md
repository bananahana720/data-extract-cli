# Build Assets

This directory contains build assets for the Windows installer and executable branding.

## Required Files

### icon.ico

The application icon used throughout the installer and application.

**Specifications:**
- Format: ICO (Windows icon format)
- Recommended sizes: 256x256, 48x48, 32x32, 16x16 pixels
- Used for:
  - Executable file icon
  - Desktop shortcut icon
  - Start Menu icon
  - Windows Explorer display
  - Taskbar preview

**Status:** Currently using default PyInstaller icon. Replace with custom icon for branded builds.

## Creating Custom Icons

### Method 1: Online Converter

1. Create a PNG image at 256x256 pixels
2. Use online ICO converter (e.g., [convertio.co](https://convertio.co/) or [icoconvert.com](https://icoconvert.com/))
3. Upload PNG file
4. Download as ICO with auto-resize enabled
5. Place `icon.ico` in this directory

### Method 2: ImageMagick (Command Line)

```bash
# Install ImageMagick (Windows)
choco install imagemagick

# Convert PNG to ICO with automatic resizing
convert icon.png -define icon:auto-resize=256,48,32,16 icon.ico
```

### Method 3: Python (pillow)

```python
from PIL import Image

# Open PNG file
img = Image.open('icon.png')

# Create ICO with multiple sizes
img.save('icon.ico', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
```

## Integration with Build System

Once `icon.ico` is placed in this directory:

1. The build script automatically detects and uses the custom icon
2. Update `build_scripts/installer.iss` if needed:
   ```ini
   [Setup]
   SetupIconFile=assets\icon.ico
   ```

3. Rebuild the executable:
   ```powershell
   .\build_scripts\build_windows.ps1 -Clean
   ```

## Design Guidelines

For best results when creating a custom icon:

- Use clean, simple design (icons scale down to 16x16)
- Avoid thin lines that disappear at small sizes
- Use solid colors or simple gradients
- Maintain sufficient contrast
- Consider how the icon looks on both light and dark backgrounds
- Include app name or abbreviation at larger sizes (256/128)
- Keep smaller versions (16/32) simple and recognizable

## Example Icon Directory Structure

Once complete:

```
build_scripts/
├── assets/
│   ├── README.md
│   └── icon.ico          # Custom application icon
├── BUILD.md
├── build_windows.ps1
└── ...
```

## Current Status

**Development**: Using default PyInstaller icon
**Production Ready**: Requires custom icon.ico file in this directory

See `/home/andrew/dev/data-extraction-tool/build_scripts/BUILD.md` for complete build documentation.
