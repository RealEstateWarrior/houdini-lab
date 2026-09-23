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
    [string]$Out = "out\houdini_window.png",
    [int]$ProcessId = 0
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
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc cb, IntPtr lp);
  [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetWindowText(IntPtr h, System.Text.StringBuilder s, int n);
  delegate bool EnumProc(IntPtr h, IntPtr lp);

  // The process can own several top-level windows (the main window, the
  // "Houdini Console", floating panes). MainWindowHandle picks whichever was
  // active last, which was the console. Pick the largest visible window whose
  // title is not the console instead.
  public static IntPtr FindMain(uint[] pids) {
    IntPtr best = IntPtr.Zero; long bestArea = 0;
    EnumWindows(delegate (IntPtr h, IntPtr lp) {
      uint pid; GetWindowThreadProcessId(h, out pid);
      if (Array.IndexOf(pids, pid) < 0 || !IsWindowVisible(h)) return true;
      var sb = new System.Text.StringBuilder(512); GetWindowText(h, sb, 512);
      string t = sb.ToString();
      if (t.Length == 0 || t.IndexOf("Console", StringComparison.OrdinalIgnoreCase) >= 0) return true;
      RECT r; GetWindowRect(h, out r);
      long a = (long)(r.Right - r.Left) * (r.Bottom - r.Top);
      if (a > bestArea) { bestArea = a; best = h; }
      return true;
    }, IntPtr.Zero);
    return best;
  }
  public static string Title(IntPtr h) {
    var sb = new System.Text.StringBuilder(512); GetWindowText(h, sb, 512); return sb.ToString();
  }
}
'@
if (-not ("WinCap" -as [type])) { Add-Type -TypeDefinition $signature }

# Without this, GetWindowRect returns physical pixels while CopyFromScreen works
# in scaled coordinates, so the captured region is offset and the wrong size.
[WinCap]::SetProcessDPIAware() | Out-Null

$procs = @(Get-Process $ProcessName -ErrorAction SilentlyContinue)
if ($procs.Count -eq 0) {
    Write-Output "no process found: $ProcessName"
    exit 1
}
$pids = [uint32[]]($procs | ForEach-Object { [uint32]$_.Id })
# Houdini が2つ起動していると、大きいほうの窓（受け口の無いほう）を撮ってしまう。番号が分かればそれだけに絞る
if ($ProcessId -gt 0) { $pids = [uint32[]]@([uint32]$ProcessId) }
$handle = [WinCap]::FindMain($pids)
if ($handle -eq [IntPtr]::Zero) {
    Write-Output "no visible main window found for process: $ProcessName"
    exit 1
}
# Maximise before capturing. GetWindowRect on a partially covered window still
# returns the full rect, so anything overlapping it ends up in the screenshot.
[WinCap]::ShowWindow($handle, 3) | Out-Null       # SW_MAXIMIZE
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

if ([System.IO.Path]::IsPathRooted($Out)) {
    $full = [System.IO.Path]::GetFullPath($Out)
} else {
    $full = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $Out))
}
$dir = [System.IO.Path]::GetDirectoryName($full)
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
$bitmap.Save($full, [System.Drawing.Imaging.ImageFormat]::Png)
$bitmap.Dispose()

Write-Output ("saved: {0}" -f $full)
Write-Output ("size: {0} by {1}" -f $width, $height)
Write-Output ("title: {0}" -f [WinCap]::Title($handle))
