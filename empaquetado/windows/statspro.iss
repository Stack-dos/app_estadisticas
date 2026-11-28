; Instalador de Windows (US-109, AC9): toma la carpeta que arma "flet build windows" y la empaqueta en un .exe.
; Lo compila release.yml con el Inno Setup que trae windows-latest:
;   ISCC.exe /DVersion=0.1.0 /DCarpetaApp=<build\windows> /DSalida=<dist> empaquetado\windows\statspro.iss
; Las rutas se pasan absolutas: Inno Setup resuelve las relativas desde la carpeta de este archivo.
;
; Desinstalar borra la app, pero NO ~/.statspro/ (la base del usuario): una reinstalacion o una version nueva
; encuentran los datos donde estaban.

#ifndef Version
  #define Version "0.0.0"
#endif
#ifndef CarpetaApp
  #error Falta /DCarpetaApp=<carpeta de flet build windows>
#endif
#ifndef Salida
  #define Salida "."
#endif

[Setup]
; Identifica la app entre versiones: con el mismo AppId, instalar una version nueva reemplaza la anterior.
; No cambiarlo nunca.
AppId={{7DCE0765-B57B-4574-821B-82DD8A778A6A}
AppName=StatsPro
AppVersion={#Version}
AppPublisher=StatsPro
AppPublisherURL=https://github.com/nicopinera/app_estadisticas
DefaultDirName={autopf}\StatsPro
DefaultGroupName=StatsPro
DisableProgramGroupPage=yes
; Pregunta si instalar para todos (pide admin) o solo para este usuario (no pide admin)
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#Salida}
OutputBaseFilename=StatsPro-{#Version}-windows-x64-instalador
UninstallDisplayIcon={app}\StatsPro.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "escritorio"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#CarpetaApp}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\StatsPro"; Filename: "{app}\StatsPro.exe"
Name: "{autodesktop}\StatsPro"; Filename: "{app}\StatsPro.exe"; Tasks: escritorio

[Run]
Filename: "{app}\StatsPro.exe"; Description: "{cm:LaunchProgram,StatsPro}"; Flags: nowait postinstall skipifsilent
