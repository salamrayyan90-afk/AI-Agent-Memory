# Create/update Core AI desktop shortcut with new icon
$ProjectPath = "C:\Users\user\Desktop\Core AI"
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "Core AI.lnk"
$IconPath = Join-Path $ProjectPath "icon.ico"
$BatPath = Join-Path $ProjectPath "run.bat"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $BatPath
$Shortcut.WorkingDirectory = $ProjectPath
$Shortcut.Description = "Core AI - 2026"
if (Test-Path $IconPath) { $Shortcut.IconLocation = $IconPath }
$Shortcut.Save()
Write-Host "Desktop shortcut updated: $ShortcutPath"
