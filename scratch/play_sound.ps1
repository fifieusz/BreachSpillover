Add-Type -AssemblyName presentationCore
$p = New-Object System.Windows.Media.MediaPlayer
$soundPath = (Resolve-Path "frontend/static/sounds/Clickingsound.mp3").Path
$p.Open([System.Uri]$soundPath)
Start-Sleep -Milliseconds 400
$p.Play()
Start-Sleep -Milliseconds 2200
