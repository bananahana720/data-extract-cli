# Build Scripts

This directory contains build and packaging scripts for the Data Extraction Tool.

## Windows Installer (Inno Setup)

### Prerequisites

1. **Inno Setup 6.x**: Download from [https://jrsoftware.org/isdl.php](https://jrsoftware.org/isdl.php)
2. **PyInstaller build**: The installer expects a PyInstaller build in `dist/data-extract/`

### Building the PyInstaller Executable

Before creating the installer, build the standalone executable:

```bash
# Install PyInstaller (if not already installed)
pip install pyinstaller

# Build the executable
pyinstaller --name data-extract \
    --onedir \
    --console \
    --add-data "src/data_extract:data_extract" \
    --hidden-import data_extract \
    --hidden-import spacy \
    --hidden-import sklearn \
    src/data_extract/cli/main.py
```

This creates `dist/data-extract/` with all necessary files.

### Building the Installer

#### Using Inno Setup GUI (Windows)

1. Open Inno Setup Compiler
2. File → Open → Select `build_scripts/installer.iss`
3. Build → Compile (or press F9)
4. Installer will be created in `dist/installer/DataExtractionTool-Setup-1.0.0.exe`

#### Using Command Line (Windows)

```cmd
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" build_scripts\installer.iss
```

### Installer Features

**Installation Options:**
- **Per-user installation** (no admin rights required)
- Desktop shortcut (optional, checked by default)
- Start menu entry (optional, checked by default)
- Add to PATH (optional, checked by default)

**PATH Management:**
- Automatically adds installation directory to user PATH
- Checks for existing PATH entries to prevent duplicates
- Removes from PATH on uninstall

**Configuration Data:**
- On uninstall, prompts user to keep or remove configuration data
- Config location: `%APPDATA%\data-extraction-tool`
- Allows preserving settings across reinstalls

**System Requirements:**
- Windows 10 or later
- No admin privileges required (per-user install)
- ~500 MB disk space

### Customization

Edit `build_scripts/installer.iss` to customize:

- **AppVersion**: Line 6 - Update version number
- **AppURL**: Line 8 - Update project URL
- **AppId**: Line 13 - Generate new GUID for forked projects
- **OutputDir**: Line 28 - Change installer output location
- **Compression**: Line 34 - Adjust compression settings

### Testing the Installer

1. **Clean test**: Test on a machine without the tool installed
2. **Verify PATH**: After install, open new CMD and run `data-extract --help`
3. **Verify shortcuts**: Check desktop and start menu icons work
4. **Verify uninstall**:
   - Uninstall and verify PATH removal
   - Check config data prompt appears
   - Verify clean removal of files

### Troubleshooting

**"Cannot find dist\data-extract" error:**
- Build the PyInstaller executable first (see above)
- Verify `dist/data-extract/data-extract.exe` exists

**PATH not working after install:**
- Open a NEW command prompt (PATH changes don't affect existing sessions)
- Or log out and log back in
- Verify PATH: `echo %PATH%` should contain installation directory

**Admin rights prompt:**
- If prompted for admin rights, the `PrivilegesRequired=lowest` setting may need verification
- This should NOT happen - installer is designed for per-user install

## Future Enhancements

Possible additions for future versions:

- **Silent install**: Add `/SILENT` and `/VERYSILENT` command-line support
- **Auto-update**: Add version check and update mechanism
- **Custom icons**: Replace default icon with branded icon
- **License agreement**: Add LICENSE file and enable LicenseFile option
- **README display**: Add README.md display before installation
