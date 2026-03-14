Dim fso, dir, pythonw, script
Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
pythonw = dir & "\.venv\Scripts\pythonw.exe"
script  = dir & "\main.py"

CreateObject("WScript.Shell").Run Chr(34) & pythonw & Chr(34) & " " & Chr(34) & script & Chr(34), 0, False
