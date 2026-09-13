# Capture the window of a running application (e.g. the Houdini GUI) to a PNG.
#
# NOTE: comments here are ASCII on purpose. Windows PowerShell 5.1 reads a .ps1
# without a BOM as ANSI, so non-ASCII characters corrupt the parse and produce
# misleading syntax errors far from the real cause.
#
# OpenGL windows usually come out black with PrintWindow, so this brings the
# window to the front and copies from the screen instead.
#
#   powershell -ExecutionPolicy Bypass -File capture_window.ps1 -Out out\shot.png

param(
    [string]$ProcessName = "houdini",
    [string]$Out = "out\houdini_window.png"
)

Add-Type -AssemblyName System.Drawing

$signature = @'
using System;
using System.Runtime.InteropServices;
public class WinCap {
  [StructLayout(LayoutKind.Sequential)]
  public struct RECT { public int Left, Top, Right, Bottom; }
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n);
}
'@
if (-not ("WinCap" -as [type])) { Add-Type -TypeDefinition $signature }

$process = Get-Process $ProcessName -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
if (-not $process) {
    Write-Output "no visible window found for process: $ProcessName"
    exit 1
}

$handle = $process.MainWindowHandle
[WinCap]::ShowWindow($handle, 9) | Out-Null       # restore if minimised
[WinCap]::SetForegroundWindow($handle) | Out-Null
Start-Sleep -Milliseconds 900                     # let it repaint

$rect = New-Object WinCap+RECT
[WinCap]::GetWindowRect($handle, [ref]$rect) | Out-Null
$width = $rect.Right - $rect.Left
$height = $rect.Bottom - $rect.Top
if ($width -le 0 -or $height -le 0) {
    Write-Output "could not read the window size"
    exit 1
}

$bitmap = New-Object System.Drawing.Bitmap $width, $height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $bitmap.Size)
$graphics.Dispose()

$full = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $Out))
$dir = [System.IO.Path]::GetDirectoryName($full)
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
$bitmap.Save($full, [System.Drawing.Imaging.ImageFormat]::Png)
$bitmap.Dispose()

Write-Output ("saved: {0}" -f $full)
Write-Output ("size: {0} by {1}" -f $width, $height)
Write-Output ("title: {0}" -f $process.MainWindowTitle)
