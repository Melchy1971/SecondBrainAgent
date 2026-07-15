; Inno Setup script for Jarvis.
; Produces a per-user installer by default; the privilege dialog optionally
; enables a standard system-wide installation.
; creates desktop + start-menu shortcuts and an uninstaller, keeps all user data
; in %APPDATA%\Jarvis (survives updates), runs a post-install smoke test, and on
; uninstall removes the program but keeps user data unless the user confirms.
;
; Build:  iscc /DAppVersion=30.77.0 installer.iss
; Expects the PyInstaller output at: ..\..\dist\Jarvis\

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#define AppName "Jarvis"
#define AppPublisher "SecondBrain"
#define AppExe "Jarvis.exe"
#define CliExe "jarvis-cli.exe"

[Setup]
AppId={{B7D6B9E4-9C2E-4A6F-9E1B-JARVIS000001}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={code:GetDefaultDirName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#AppExe}
OutputDir=..\..\dist\release
OutputBaseFilename=Jarvis-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog commandline
CloseApplications=yes
RestartApplications=no
UsePreviousAppDir=yes
UsePreviousTasks=yes

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "autostart"; Description: "Jarvis automatisch mit Windows starten"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\dist\Jarvis\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Dirs]
; User data root - never removed by an uninstall unless the user opts in (see [Code]).
Name: "{userappdata}\{#AppName}"; Flags: uninsneveruninstall
Name: "{userappdata}\{#AppName}\config"; Flags: uninsneveruninstall
Name: "{userappdata}\{#AppName}\data"; Flags: uninsneveruninstall
Name: "{userappdata}\{#AppName}\database"; Flags: uninsneveruninstall
Name: "{userappdata}\{#AppName}\vault"; Flags: uninsneveruninstall
Name: "{userappdata}\{#AppName}\backups"; Flags: uninsneveruninstall
Name: "{localappdata}\{#AppName}\logs"; Flags: uninsneveruninstall
Name: "{localappdata}\{#AppName}\cache"; Flags: uninsneveruninstall
Name: "{localappdata}\{#AppName}\updates"; Flags: uninsneveruninstall
Name: "{localappdata}\{#AppName}\runtime"; Flags: uninsneveruninstall

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"; Comment: "Jarvis native GUI"
Name: "{group}\Jarvis Web HUD"; Filename: "{app}\{#AppExe}"; Parameters: "hud"; Comment: "Jarvis Web HUD"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon
Name: "{userstartup}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: autostart

[Registry]
Root: HKA; Subkey: "Software\SecondBrain\Jarvis"; ValueType: string; ValueName: "Version"; ValueData: "{#AppVersion}"; Flags: uninsdeletekey

[Run]
; Post-install smoke test. A non-zero exit surfaces a warning to the user.
Filename: "{app}\{#CliExe}"; Parameters: "smoke-test"; StatusMsg: "Smoke-Test laeuft ..."; Flags: runhidden waituntilterminated; Check: RunSmokeTest
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[Code]
var
  SmokeExitCode: Integer;

function GetDefaultDirName(Param: String): String;
begin
  if IsAdminInstallMode then
    Result := ExpandConstant('{autopf}\{#AppName}')
  else
    Result := ExpandConstant('{localappdata}\Programs\{#AppName}');
end;

function NextVersionPart(var Value: String): Integer;
var
  Separator: Integer;
  Part: String;
begin
  Separator := Pos('.', Value);
  if Separator = 0 then
  begin
    Part := Value;
    Value := '';
  end
  else
  begin
    Part := Copy(Value, 1, Separator - 1);
    Delete(Value, 1, Separator);
  end;
  Result := StrToIntDef(Part, 0);
end;

function CompareVersions(Left, Right: String): Integer;
var
  Index, LeftPart, RightPart: Integer;
begin
  Result := 0;
  for Index := 1 to 4 do
  begin
    LeftPart := NextVersionPart(Left);
    RightPart := NextVersionPart(Right);
    if LeftPart > RightPart then begin Result := 1; Exit; end;
    if LeftPart < RightPart then begin Result := -1; Exit; end;
  end;
end;

function InitializeSetup(): Boolean;
var
  InstalledVersion: String;
begin
  Result := True;
  if not RegQueryStringValue(HKCU, 'Software\SecondBrain\Jarvis', 'Version', InstalledVersion) then
    RegQueryStringValue(HKLM64, 'Software\SecondBrain\Jarvis', 'Version', InstalledVersion);
  if (InstalledVersion <> '') and (CompareVersions(InstalledVersion, '{#AppVersion}') > 0) then
  begin
    MsgBox('Downgrade blockiert: Installiert ist ' + InstalledVersion +
      ', das Paket enthaelt {#AppVersion}.', mbError, MB_OK);
    Result := False;
  end;
end;

function RunSmokeTest: Boolean;
var
  ResultCode: Integer;
begin
  Result := False; { do not also run via [Run]; we execute here to capture the code }
  if Exec(ExpandConstant('{app}\{#CliExe}'), 'smoke-test', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    SmokeExitCode := ResultCode
  else
    SmokeExitCode := -1;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    RunSmokeTest();
    if SmokeExitCode <> 0 then
      MsgBox('Der Smoke-Test ist fehlgeschlagen (Code ' + IntToStr(SmokeExitCode) +
             '). Die Installation wurde abgeschlossen, aber Jarvis startet moeglicherweise nicht korrekt.',
             mbError, MB_OK);
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir, LocalDataDir: String;
begin
  if CurUninstallStep = usUninstall then
  begin
    DataDir := ExpandConstant('{userappdata}\{#AppName}');
    LocalDataDir := ExpandConstant('{localappdata}\{#AppName}');
    if DirExists(DataDir) then
    begin
      if MsgBox('Sollen die Jarvis-Nutzerdaten (Konfiguration, Vault, Dokumente) unter' + #13#10 +
                DataDir + #13#10 + 'ebenfalls entfernt werden?' + #13#10#13#10 +
                'Ja = alles loeschen   /   Nein = Daten behalten',
                mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
      begin
        DelTree(DataDir, True, True, True);
        DelTree(LocalDataDir, True, True, True);
      end;
    end;
  end;
end;
