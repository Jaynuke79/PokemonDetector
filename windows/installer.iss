; Inno Setup script for the Pokemon Detector installer.
; Build windows\dist\PokemonDetector with poke.spec first, then compile with:
;   ISCC /DAppVersion=<version from pyproject.toml> installer.iss

#ifndef AppVersion
  #error Pass the version on the command line: ISCC /DAppVersion=<version> installer.iss
#endif

[Setup]
AppId={{DD72EEE3-77EF-41BE-9D33-F16BA27FAEDD}
AppName=Pokemon Detector
AppVersion={#AppVersion}
AppVerName=Pokemon Detector {#AppVersion}
DefaultDirName={localappdata}\Programs\PokemonDetector
DefaultGroupName=Pokemon Detector
AppMutex=PokemonDetectorWebLauncher
MinVersion=10.0
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
ChangesEnvironment=yes
WizardStyle=modern
DisableWelcomePage=no
DisableDirPage=auto
DisableProgramGroupPage=yes
DisableReadyPage=yes
OutputDir=installer_output
OutputBaseFilename=PokemonDetectorSetup-{#AppVersion}
Compression=lzma2
UninstallDisplayName=Pokemon Detector
UninstallDisplayIcon={app}\PokemonDetector.exe

[Tasks]
Name: "addtopath"; Description: "Add Pokemon Detector to my PATH, so ""poke"" works in any new terminal"
Name: "desktopicon"; Description: "Create a desktop icon"; Flags: unchecked

; Files from an older version's bundle must not be left next to the new ones.
[InstallDelete]
Type: filesandordirs; Name: "{app}\_internal"; Check: IsExistingInstall

[Files]
Source: "dist\PokemonDetector\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Pokemon Detector"; Filename: "{app}\PokemonDetector.exe"; WorkingDir: "{app}"
Name: "{group}\Pokemon Detector CLI"; Filename: "{cmd}"; Parameters: "/K echo Usage: poke path\to\image.png"; WorkingDir: "{app}"
Name: "{group}\Uninstall Pokemon Detector"; Filename: "{uninstallexe}"
Name: "{userdesktop}\Pokemon Detector"; Filename: "{app}\PokemonDetector.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\PokemonDetector.exe"; Description: "Launch Pokemon Detector"; Flags: postinstall nowait skipifsilent

[Code]
const
  EnvironmentKey = 'Environment';
  PathValue = 'Path';

// A folder chosen in the wizard can belong to another app with its own _internal.
function IsExistingInstall: Boolean;
begin
  Result := FileExists(ExpandConstant('{app}\PokemonDetector.exe'));
end;

function ReadUserPath(var UserPath: String): Boolean;
begin
  UserPath := '';
  Result := not RegValueExists(HKEY_CURRENT_USER, EnvironmentKey, PathValue)
    or RegQueryStringValue(HKEY_CURRENT_USER, EnvironmentKey, PathValue, UserPath);
  if not Result then
    Log('User PATH is not a string value, leaving it alone');
end;

// Wrapping the value in separators means only whole entries can match, so
// "C:\Apps\Poke" is never found inside "C:\Apps\Poke2".
function WholeEntryPos(const Entry, WrappedPath: String): Integer;
begin
  Result := Pos(';' + AnsiUppercase(Entry) + ';', AnsiUppercase(WrappedPath));
end;

function RemoveWholeEntry(const Entry: String; var WrappedPath: String): Boolean;
var
  EntryPos: Integer;
begin
  Result := False;
  EntryPos := WholeEntryPos(Entry, WrappedPath);
  while EntryPos > 0 do
  begin
    Delete(WrappedPath, EntryPos, Length(Entry) + 1);
    Result := True;
    EntryPos := WholeEntryPos(Entry, WrappedPath);
  end;
end;

procedure WriteUserPath(const UserPath: String);
begin
  if UserPath = '' then
    RegDeleteValue(HKEY_CURRENT_USER, EnvironmentKey, PathValue)
  // RegWriteStringValue keeps an existing REG_EXPAND_SZ value's type.
  else if not RegWriteStringValue(HKEY_CURRENT_USER, EnvironmentKey, PathValue, UserPath) then
    Log('Could not write the user PATH');
end;

procedure AddAppToUserPath;
var
  UserPath, AppDir: String;
begin
  if not ReadUserPath(UserPath) then
    Exit;
  AppDir := ExpandConstant('{app}');
  if (WholeEntryPos(AppDir, ';' + UserPath + ';') > 0)
    or (WholeEntryPos(AppDir + '\', ';' + UserPath + ';') > 0) then
    Exit;
  if (UserPath <> '') and (UserPath[Length(UserPath)] <> ';') then
    UserPath := UserPath + ';';
  WriteUserPath(UserPath + AppDir);
end;

procedure RemoveAppFromUserPath;
var
  UserPath, WrappedPath, AppDir: String;
  RemovedPlain, RemovedWithBackslash: Boolean;
begin
  if not ReadUserPath(UserPath) then
    Exit;
  AppDir := ExpandConstant('{app}');
  WrappedPath := ';' + UserPath + ';';
  RemovedPlain := RemoveWholeEntry(AppDir, WrappedPath);
  RemovedWithBackslash := RemoveWholeEntry(AppDir + '\', WrappedPath);
  if RemovedPlain or RemovedWithBackslash then
    WriteUserPath(Copy(WrappedPath, 2, Length(WrappedPath) - 2));
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if WizardIsTaskSelected('addtopath') then
      AddAppToUserPath
    else
      RemoveAppFromUserPath;
  end;
end;

// usUninstall comes before the uninstaller's environment change notification.
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
    RemoveAppFromUserPath;
end;
