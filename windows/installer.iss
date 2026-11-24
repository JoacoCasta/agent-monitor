[Setup]
AppId={{8D6B2A1E-9C4F-4E31-B8B1-52F0F1C7E201}
AppName=Agent Monitor
AppVersion=2.2.0
AppPublisher=Agent Monitor Contributors
AppPublisherURL=https://github.com/JoacoCasta/agent-monitor
DefaultDirName={localappdata}\Programs\Agent Monitor
DefaultGroupName=Agent Monitor
PrivilegesRequired=lowest
OutputDir=..\dist\installer
OutputBaseFilename=AgentMonitor-Windows-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\AgentMonitor.exe

[Tasks]
Name: "startupicon"; Description: "Start Agent Monitor when Windows starts"; GroupDescription: "Additional options:"

[Files]
Source: "..\dist\AgentMonitor.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\Scripts\*.py"; DestDir: "{app}\Scripts"; Flags: ignoreversion

[Icons]
Name: "{group}\Agent Monitor"; Filename: "{app}\AgentMonitor.exe"
Name: "{group}\Uninstall Agent Monitor"; Filename: "{uninstallexe}"
Name: "{userstartup}\Agent Monitor"; Filename: "{app}\AgentMonitor.exe"; Tasks: startupicon

[Run]
Filename: "{app}\AgentMonitor.exe"; Description: "Launch Agent Monitor"; Flags: nowait postinstall skipifsilent
