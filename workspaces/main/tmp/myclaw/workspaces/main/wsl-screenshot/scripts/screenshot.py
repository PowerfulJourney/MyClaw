#!/usr/bin/env python3
"""
WSL Screenshot Tool
Captures full-screen screenshot in WSL2 using Windows Graphics API.
"""

import subprocess
import sys
import os
from pathlib import Path


def check_wsl():
    """Check if running in WSL2."""
    try:
        with open('/proc/version', 'r') as f:
            return 'microsoft' in f.read().lower()
    except:
        return False


def get_powershell_path():
    """Find PowerShell executable in WSL."""
    # Common PowerShell paths in WSL
    paths = [
        '/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe',
        '/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell',
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    # Try which
    try:
        result = subprocess.run(['which', 'powershell.exe'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return None


def capture_screenshot(output_path=None):
    """
    Capture screenshot using PowerShell + .NET Graphics API.
    
    Args:
        output_path: Where to save the PNG file. If None, saves to current directory.
    
    Returns:
        Path to the saved screenshot
    """
    if not check_wsl():
        raise RuntimeError("This tool only works in WSL2. For native Linux, use scrot or grim.")
    
    powershell = get_powershell_path()
    if not powershell:
        raise RuntimeError("PowerShell not found. Ensure Windows is accessible from WSL.")
    
    # Default output path
    if output_path is None:
        output_path = os.path.expanduser('~/.openclaw/workspace/screenshot.png')
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Windows path for PowerShell
    # Convert /mnt/c/Users/... to C:/Users/... then to C:\Users\...
    win_path = str(output_path)
    if win_path.startswith('/mnt/'):
        # /mnt/c/... -> C:/...
        parts = win_path.split('/')
        if len(parts) >= 3 and len(parts[2]) == 1:
            drive = parts[2].upper()
            win_path = f"{drive}:/{'/'.join(parts[3:])}"
    # Convert forward slashes to backslashes for Windows
    win_path = win_path.replace('/', '\\')
    
    # PowerShell script for DPI-aware screenshot
    ps_script = f"""
[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null
[System.Reflection.Assembly]::LoadWithPartialName('System.Drawing') | Out-Null

# Enable DPI awareness
$type = Add-Type -MemberDefinition '[DllImport(\"user32.dll\")] public static extern bool SetProcessDPIAware();' -Name Win32 -Namespace Native -PassThru
$type::SetProcessDPIAware() | Out-Null
Start-Sleep -m 300

$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
$bitmap.Save('{win_path}')
Write-Output "Screenshot: $($screen.Width)x$($screen.Height)"
"""
    
    # Execute PowerShell
    result = subprocess.run(
        [powershell, '-Command', ps_script],
        capture_output=True
    )
    
    # Decode output handling different encodings
    try:
        stdout = result.stdout.decode('utf-8')
    except UnicodeDecodeError:
        try:
            stdout = result.stdout.decode('gbk')  # Chinese Windows
        except:
            stdout = result.stdout.decode('utf-8', errors='ignore')
    
    try:
        stderr = result.stderr.decode('utf-8')
    except UnicodeDecodeError:
        try:
            stderr = result.stderr.decode('gbk')
        except:
            stderr = result.stderr.decode('utf-8', errors='ignore')
    
    if result.returncode != 0:
        raise RuntimeError(f"Screenshot failed: {stderr}")
    
    print(stdout.strip())
    return str(output_path)


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Capture WSL2 screenshot')
    parser.add_argument('-o', '--output', help='Output file path (default: ~/screenshot.png)')
    args = parser.parse_args()
    
    try:
        path = capture_screenshot(args.output)
        print(f"Screenshot saved: {path}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
