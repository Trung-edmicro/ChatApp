[Setup]
AppName=ChatApp
AppVersion=0.0.5
DefaultDirName={pf}\ChatApp
DefaultGroupName=ChatApp
OutputDir=Output
OutputBaseFilename=ChatApp_Installer
SetupIconFile=edmicro.ico
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\chatapp\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\ChatApp"; Filename: "{app}\chatapp.exe"; IconFilename: "{app}\edmicro.ico"
Name: "{commondesktop}\ChatApp"; Filename: "{app}\chatapp.exe"; IconFilename: "{app}\edmicro.ico" ;

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"; ValueType: string; ValueName: "{app}\chatapp.exe"; ValueData: "RUNASADMIN"; Flags: uninsdeletevalue