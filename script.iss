[Setup]
AppName=Edmicro_ChatNoob
AppVersion=0.0.5
DefaultDirName={pf}\Edmicro_ChatNoob
DefaultGroupName=Edmicro_ChatNoob
OutputDir=Output
OutputBaseFilename=ChatApp_Installer
SetupIconFile=edmicro.ico
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\chatapp\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Edmicro ChatNoob"; Filename: "{app}\chatapp.exe"; IconFilename: "{app}\edmicro.ico"
Name: "{commondesktop}\Edmicro ChatNoob"; Filename: "{app}\chatapp.exe"; IconFilename: "{app}\edmicro.ico" ;

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"; ValueType: string; ValueName: "{app}\chatapp.exe"; ValueData: "RUNASADMIN"; Flags: uninsdeletevalue