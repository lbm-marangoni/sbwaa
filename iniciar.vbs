Dim shell, fso, root, obsidian

Set fso   = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

root     = fso.GetParentFolderName(WScript.ScriptFullName)
obsidian = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Obsidian\Obsidian.exe"

' 0. Splash screen (fecha sozinho apos DELAY segundos)
shell.Run "cmd /c python """ & root & "\interface\splash.py""", 1, False

WScript.Sleep 500

' 1. Obsidian
shell.Run """" & obsidian & """", 1, False

WScript.Sleep 2000

' 2. VS Code (Claude Code abre automaticamente pelo folderOpen task)
shell.Run "code """ & root & """", 0, False

WScript.Sleep 1000

' 3. Painel SBWAA (pythonw = sem janela de console)
shell.Run "pythonw """ & root & "\interface\ui.py""", 0, False
