; Data Extraction Tool - Inno Setup Installer Script
; Version: 1.0.0
; Description: Windows installer for Data Extraction Tool enterprise document processing pipeline

; TODO: Consider using Inno Setup preprocessor to read from version.py
; For now, update this manually when version.py changes
; Reference: build_scripts/version.py (__version__ = "1.0.0")

#define MyAppName "Data Extraction Tool"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Data Extraction Tool"
#define MyAppURL "https://github.com/yourusername/data-extraction-tool"
#define MyAppExeName "data-extract.exe"

[Setup]
; Application Information
AppId={{8D3F5E7A-9B2C-4F1A-A8E6-1C5D7B9F3A2E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installation Directories
DefaultDirName={autopf}\DataExtractionTool
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=no

; Output Configuration
OutputDir=dist\installer
OutputBaseFilename=DataExtractionTool-Setup-{#MyAppVersion}
SetupIconFile=compiler:SetupClassicIcon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

; Compression
Compression=lzma2/ultra64
SolidCompression=yes

; Privileges - CRITICAL: Per-user install, no admin required
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Requirements
MinVersion=10.0
WizardStyle=modern

; Architecture
ArchitecturesInstallIn64BitMode=x64compatible

; License and Documentation (optional - uncomment if files exist)
;LicenseFile=LICENSE
;InfoBeforeFile=README.md

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkablealone checked
Name: "startmenuicon"; Description: "Create Start Menu entry"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkablealone checked
Name: "addtopath"; Description: "Add to PATH (allows running 'data-extract' from command line)"; GroupDescription: "System Integration:"; Flags: checkablealone checked

[Files]
Source: "dist\data-extract\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
; Desktop shortcut
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startmenuicon
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
; Uninstall shortcut
Name: "{autoprograms}\{#MyAppName}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"; Tasks: startmenuicon

[Registry]
; Add to user PATH (HKCU, not HKLM - per-user install)
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Check: NeedsAddPath('{app}'); Flags: preservestringtype; Tasks: addtopath

[Run]
; Post-install option to launch application
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent shellexec

[UninstallDelete]
; Clean up any generated files that might not be tracked
Type: filesandordirs; Name: "{app}\__pycache__"
Type: filesandordirs; Name: "{app}\*.pyc"

[Code]
var
  RemoveConfigPage: TInputOptionWizardPage;

{ Check if path already contains the application directory }
function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
  ParamExpanded: string;
begin
  // Expand the setup constants like {app} from Param
  ParamExpanded := ExpandConstant(Param);
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OrigPath) then
  begin
    Result := True;
    exit;
  end;
  // Look for the path with leading and trailing semicolon and with or without \ ending
  // Pos() returns 0 if not found
  Result := Pos(';' + UpperCase(ParamExpanded) + ';', ';' + UpperCase(OrigPath) + ';') = 0;
  if Result = True then
    Result := Pos(';' + UpperCase(ParamExpanded) + '\;', ';' + UpperCase(OrigPath) + ';') = 0;
end;

{ Remove path from PATH environment variable on uninstall }
procedure RemovePathFromEnvironment(Path: string);
var
  OrigPath: string;
  NewPath: string;
  PathUpper: string;
  OrigPathUpper: string;
  StartPos: Integer;
  EndPos: Integer;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OrigPath) then
  begin
    exit;
  end;

  PathUpper := UpperCase(Path);
  OrigPathUpper := UpperCase(OrigPath);
  NewPath := OrigPath;

  // Try to find path with trailing backslash
  StartPos := Pos(PathUpper + '\;', OrigPathUpper);
  if StartPos > 0 then
  begin
    EndPos := StartPos + Length(Path) + 1; // +1 for backslash
    // Remove including the semicolon
    Delete(NewPath, StartPos, Length(Path) + 2); // +2 for backslash and semicolon
  end
  else
  begin
    // Try to find path without trailing backslash
    StartPos := Pos(PathUpper + ';', OrigPathUpper);
    if StartPos > 0 then
    begin
      EndPos := StartPos + Length(Path);
      // Remove including the semicolon
      Delete(NewPath, StartPos, Length(Path) + 1); // +1 for semicolon
    end;
  end;

  // Clean up any double semicolons
  while Pos(';;', NewPath) > 0 do
  begin
    StringChangeEx(NewPath, ';;', ';', True);
  end;

  // Remove leading/trailing semicolons
  if (Length(NewPath) > 0) and (NewPath[1] = ';') then
    Delete(NewPath, 1, 1);
  if (Length(NewPath) > 0) and (NewPath[Length(NewPath)] = ';') then
    Delete(NewPath, Length(NewPath), 1);

  // Update the registry
  if NewPath <> OrigPath then
  begin
    RegWriteExpandStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', NewPath);
  end;
end;

{ Initialize uninstall wizard }
procedure InitializeUninstallProgressForm();
begin
  // Nothing needed here for now
end;

{ Create custom uninstall page for config data }
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
  ConfigPath: string;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Remove from PATH
    RemovePathFromEnvironment(ExpandConstant('{app}'));

    // Ask about configuration data
    ConfigPath := ExpandConstant('{userappdata}\data-extraction-tool');
    if DirExists(ConfigPath) then
    begin
      if MsgBox('Do you want to remove configuration data and cache files?' + #13#10 +
                'Location: ' + ConfigPath + #13#10#13#10 +
                'Choose "Yes" to remove all settings and cached data.' + #13#10 +
                'Choose "No" to keep your settings for future installations.',
                mbConfirmation, MB_YESNO) = IDYES then
      begin
        // Use DelTree to remove directory and contents
        DelTree(ConfigPath, True, True, True);
      end;
    end;
  end;
end;

{ Wizard initialization }
procedure InitializeWizard();
begin
  // Could add custom pages here if needed
end;

{ Before installation }
function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
end;

{ After successful installation }
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Broadcast environment variable change
    if WizardIsTaskSelected('addtopath') then
    begin
      // Notify system of environment variable change
      // This makes the PATH change take effect without logout
      RegWriteStringValue(HKEY_CURRENT_USER, 'Environment', 'TEMP_NOTIFY', '1');
      RegDeleteValue(HKEY_CURRENT_USER, 'Environment', 'TEMP_NOTIFY');
    end;
  end;
end;
