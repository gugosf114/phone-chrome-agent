Start-Transcript -Path C:\Users\georg\agent-chrome-show.log -Force | Out-Null
Add-Type -Namespace N -Name W -MemberDefinition @'
[DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
[DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
[DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
'@
"this shell session: " + (Get-Process -Id $pid).SessionId
"explorer session(s): " + ((Get-Process explorer -ErrorAction SilentlyContinue | Select-Object -ExpandProperty SessionId) -join ",")
$all = Get-Process chrome -ErrorAction SilentlyContinue
"chrome processes: " + $all.Count + " in sessions: " + (($all | Select-Object -ExpandProperty SessionId | Sort-Object -Unique) -join ",")
$all | Where-Object { $_.MainWindowHandle -ne 0 } | ForEach-Object { "window pid=" + $_.Id + " session=" + $_.SessionId + " minimized=" + [N.W]::IsIconic($_.MainWindowHandle) + " title=" + $_.MainWindowTitle }
$w = $all | Where-Object { $_.MainWindowHandle -ne 0 -and ($_.MainWindowTitle -like "*LinkedIn*" -or $_.MainWindowTitle -like "*Home Depot*") } | Select-Object -First 1
if ($w) { [N.W]::ShowWindow($w.MainWindowHandle, 9) | Out-Null; [N.W]::SetForegroundWindow($w.MainWindowHandle) | Out-Null; "brought to front: " + $w.MainWindowTitle } else { "no LinkedIn/HomeDepot window handle visible from this session" }
Stop-Transcript | Out-Null
