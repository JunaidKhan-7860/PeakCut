$WshShell = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$Shortcut = $WshShell.CreateShortcut((Join-Path $desktop "PeakCut Live AI Dashboard.lnk"))
$Shortcut.TargetPath = "http://127.0.0.1:8765/dashboard"
$Shortcut.Description = "PeakCut Autonomous AI Control Center"
$Shortcut.Save()
Write-Output "PeakCut Desktop Shortcut created successfully."
