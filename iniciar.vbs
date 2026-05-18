Dim shell, fso, root, obsidian

Set fso   = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

root     = fso.GetParentFolderName(WScript.ScriptFullName)
obsidian = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Obsidian\Obsidian.exe"

' 1. Obsidian
shell.Run """" & obsidian & """", 1, False

WScript.Sleep 2000

' 2. VS Code (Claude Code abre automaticamente pelo folderOpen task)
shell.Run "code """ & root & """", 0, False

WScript.Sleep 1000

' 3. Painel SBWAA (pythonw = sem janela de console)
shell.Run "pythonw """ & root & "\ui.py""", 0, False
