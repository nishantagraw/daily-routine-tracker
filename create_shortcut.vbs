' Create Desktop Shortcut for Daily Routine Tracker
Set WshShell = WScript.CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get paths
strDesktop = WshShell.SpecialFolders("Desktop")
strAppPath = fso.GetParentFolderName(WScript.ScriptFullName)
strBatchFile = strAppPath & "\start_tracker.bat"
strShortcutPath = strDesktop & "\Routine Tracker.lnk"

' Use a built-in icon (checklist icon from shell32.dll)
strIconPath = "C:\Windows\System32\shell32.dll,76"

' Create shortcut
Set oShortcut = WshShell.CreateShortcut(strShortcutPath)
oShortcut.TargetPath = strBatchFile
oShortcut.WorkingDirectory = strAppPath
oShortcut.IconLocation = strIconPath
oShortcut.Description = "Daily Routine Tracker - Track your habits with style"
oShortcut.WindowStyle = 1
oShortcut.Save

WScript.Echo "✅ Desktop shortcut created: Routine Tracker" & vbCrLf & vbCrLf & _
             "Double-click it to start tracking your habits!"
