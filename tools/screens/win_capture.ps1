# Captures one window of a process this session started (a dev build on sandbox data) for the
# screens survey, optionally after sending it a keyboard chord. A chord is sent only while that
# window is in front, so it can never reach another app.
#
#   pwsh tools/screens/win_capture.ps1 -ProcessId 7672 -Out _screens-sources/tendril/01-pages.png [-Keys "^1"]
#   pwsh tools/screens/win_capture.ps1 -ProcessId 7672 -Width 1280 -Height 800    # resize, no capture
#
# -Keys uses System.Windows.Forms.SendKeys syntax: ^ = Ctrl, % = Alt, + = Shift.
param(
    [Parameter(Mandatory)] [int] $ProcessId,
    [string] $Out,
    [string] $Keys,
    [int[]] $Click,          # x,y relative to the window's top-left, as in a capture from this script
    [int] $Width,
    [int] $Height
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class Win {
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr dc, uint flags);
    [DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr h, int x, int y, int w, int hgt, bool repaint);
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern void mouse_event(uint f, int dx, int dy, uint d, IntPtr e);
}
"@
$h = (Get-Process -Id $ProcessId).MainWindowHandle
if ($h -eq [IntPtr]::Zero) { throw "process $ProcessId has no window" }

if ($Width -and $Height) {
    $r = New-Object Win+RECT; [void][Win]::GetWindowRect($h, [ref]$r)
    [void][Win]::MoveWindow($h, $r.L, $r.T, $Width, $Height, $true)
    Start-Sleep -Milliseconds 800
}
if ($Keys -or $Click) {
    [void][Win]::SetForegroundWindow($h)
    Start-Sleep -Milliseconds 400
    if ([Win]::GetForegroundWindow() -ne $h) { throw "window $ProcessId is not in front; no input sent" }
    if ($Click) {
        $r = New-Object Win+RECT; [void][Win]::GetWindowRect($h, [ref]$r)
        [void][Win]::SetCursorPos($r.L + $Click[0], $r.T + $Click[1])
        [Win]::mouse_event(0x2, 0, 0, 0, [IntPtr]::Zero); [Win]::mouse_event(0x4, 0, 0, 0, [IntPtr]::Zero)
        Start-Sleep -Milliseconds 300
    }
    if ($Keys) { [System.Windows.Forms.SendKeys]::SendWait($Keys) }
    Start-Sleep -Milliseconds 1200
}
if ($Out) {
    $Out = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Out)   # .NET's cwd is not PowerShell's
    $r = New-Object Win+RECT; [void][Win]::GetWindowRect($h, [ref]$r)
    $bmp = New-Object System.Drawing.Bitmap ($r.R - $r.L), ($r.B - $r.T)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $dc = $g.GetHdc()
    [void][Win]::PrintWindow($h, $dc, 2)   # PW_RENDERFULLCONTENT: works for GPU-drawn (Skia) windows
    $g.ReleaseHdc($dc); $g.Dispose()
    New-Item -ItemType Directory -Force -Path (Split-Path $Out) | Out-Null
    $bmp.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png); $bmp.Dispose()
    Write-Output $Out
}
