#define MyAppName "NEXVARY RealEstate AI OS"
#define MyAppVersion "1.4.0"
#define MyAppPublisher "NEXVARY"
#define MyAppURL "https://nexvary.com/"
#define MyAppExeName "NEXVARY-RealEstate-AI-OS.exe"

[Setup]
AppId={{F4D1E92E-20B8-46A8-9E87-26F57E4D17D3}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\NEXVARY\RealEstate AI OS
DefaultGroupName=NEXVARY RealEstate AI OS
DisableProgramGroupPage=yes
OutputDir=..\installer
OutputBaseFilename=NEXVARY-RealEstate-AI-OS-WhiteLabel-v1.4.0-Setup
SetupIconFile=nexvary-realestate.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
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
Source: "..\dist\NEXVARY-RealEstate-AI-OS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\NEXVARY RealEstate AI OS"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\NEXVARY RealEstate AI OS"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch NEXVARY RealEstate AI OS"; Flags: nowait postinstall skipifsilent
