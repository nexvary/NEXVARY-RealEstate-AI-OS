#define MyAppName "NEXVARY RealEstate AI OS"
#define MyAppVersion "2.0.0-native-preview"
#define MyAppPublisher "NEXVARY"
#define MyAppURL "https://nexvary.com/"
#define MyAppExeName "nexvary_realestate_native.exe"

[Setup]
AppId={{8E7D0B3C-6E8A-4C2E-8E85-A872C7C90850}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\NEXVARY\RealEstate AI OS Native
DefaultGroupName=NEXVARY RealEstate AI OS Native
DisableProgramGroupPage=yes
OutputDir=..\native-installer
OutputBaseFilename=NEXVARY-RealEstate-AI-OS-Native-v2.0.0-Preview-Setup
SetupIconFile=nexvary-realestate.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
InfoBeforeFile=installer-features.txt
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: checkedonce

[Files]
Source: "..\native-dist\bin\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\NEXVARY RealEstate AI OS Native"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\NEXVARY RealEstate AI OS Native"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch NEXVARY RealEstate AI OS Native"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurInstallProgressChanged(CurProgress, MaxProgress: Integer);
var
  Pct: Integer;
begin
  if MaxProgress <= 0 then Exit;
  Pct := (CurProgress * 100) div MaxProgress;
  if Pct < 18 then
    WizardForm.StatusLabel.Caption := 'Preparing native Qt 6 / C++20 workspace...'
  else if Pct < 36 then
    WizardForm.StatusLabel.Caption := 'Installing CRM, leads, inventory and enterprise finance...'
  else if Pct < 54 then
    WizardForm.StatusLabel.Caption := 'Installing AI Sales Copilot, knowledge and omnichannel tools...'
  else if Pct < 72 then
    WizardForm.StatusLabel.Caption := 'Installing Growth Intelligence, SEO Autopilot and Automation Studio...'
  else if Pct < 88 then
    WizardForm.StatusLabel.Caption := 'Preparing white-label branding, company cover and RTL interface...'
  else
    WizardForm.StatusLabel.Caption := 'Finalizing secure local API sidecar and NEXVARY runtime...';
end;
