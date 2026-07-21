; MiMo TTS - Inno Setup installer script
; Compile with Inno Setup: https://jrsoftware.org/isdl.php

#define MyAppName "MiMo-TTS"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "MiMo TTS"
#define MyAppExeName "launcher.bat"
#define MyAppMainExe "MiMo-TTS.exe"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppMainExe}
Compression=lzma2/max
SolidCompression=yes
OutputDir=..\dist
OutputBaseFilename=MiMo-TTS_Setup_v{#MyAppVersion}
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "Create desktop shortcut"; GroupDescription: "Shortcuts:"

[Files]
Source: "..\dist\MiMo-TTS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "launcher.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "install_deps.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{group}\Install Dependencies"; Filename: "{app}\install_deps.bat"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Run {#MyAppName}"; Flags: postinstall nowait skipifsilent shellexec

[Code]
function IsVCRedistInstalled: Boolean;
begin
  Result := RegKeyExists(HKLM, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\X64');
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var ResultCode: Integer;
begin
  if not IsVCRedistInstalled then
    if MsgBox('Microsoft Visual C++ Redistributable is recommended.'#13#10#13#10'Download now?', mbConfirmation, MB_YESNO) = IDYES then
      ShellExec('open', 'https://aka.ms/vs/17/release/vc_redist.x64.exe', '', '', SW_SHOW, ewNoWait, ResultCode);
  Result := '';
end;
