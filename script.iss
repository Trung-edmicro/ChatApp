[Setup]
AppName=ChatApp
AppVersion=0.0.2
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

[Run]
Filename: "{app}\chatapp.exe"; Description: "Run ChatApp"; Flags: nowait postinstall skipifsilent
