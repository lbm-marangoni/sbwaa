' SBWAA Automation — Launcher silencioso
' Invocado pelo Task Scheduler: wscript.exe launcher.vbs <slot>
' Slots válidos: morning | eod | weekend
'
' Roda o dispatcher Python sem abrir janela de console.

Option Explicit

Dim oShell, oFSO
Dim scriptDir, projectRoot, logsDir
Dim slot, cmd

Set oShell = WScript.CreateObject("WScript.Shell")
Set oFSO   = WScript.CreateObject("Scripting.FileSystemObject")

' Derivar caminhos a partir do local do .vbs (não hardcoded)
scriptDir   = oFSO.GetParentFolderName(WScript.ScriptFullName)
projectRoot = oFSO.GetParentFolderName(oFSO.GetParentFolderName(scriptDir))
logsDir     = projectRoot & "\logs"

' Criar pasta de logs se não existir
If Not oFSO.FolderExists(logsDir) Then
    oFSO.CreateFolder(logsDir)
End If

' Ler slot do argumento (padrão: morning)
If WScript.Arguments.Count > 0 Then
    slot = WScript.Arguments(0)
Else
    slot = "morning"
End If

' Montar comando: python main.py --slot <slot> >> logs\automation.log 2>&1
cmd = "cmd /c python """ & scriptDir & "\main.py"" --slot " & slot & _
      " >> """ & logsDir & "\automation.log"" 2>&1"

' Executar: 0 = janela oculta, True = aguardar conclusão
oShell.Run cmd, 0, True

Set oShell = Nothing
Set oFSO   = Nothing
