Add-Type -AssemblyName presentationCore
$mediaPlayer = New-Object System.Windows.Media.MediaPlayer
$soundPath = (Resolve-Path "frontend/static/sounds/Clickingsound.mp3").Path
$mediaPlayer.Open([System.Uri]$soundPath)
Start-Sleep -Milliseconds 800
Write-Output "Duration: $($mediaPlayer.NaturalDuration)"
Write-Output "HasAudio: $($mediaPlayer.HasAudio)"
