---
name: wsl-screenshot
description: Capture full-screen screenshots in WSL2 environment using Windows Graphics API. Use when running OpenClaw in WSL2 (Windows Subsystem for Linux) and need to capture the Windows host screen. Handles high-DPI displays correctly (2560x1600, 4K, etc.). Triggers on requests like "screenshot", "capture screen", "take a picture of my screen" when in WSL2 environment.
---

# WSL Screenshot

Capture full-screen screenshots in WSL2 using Windows Graphics API.

## When to Use

Use this skill when:
- Running OpenClaw in WSL2 (Windows Subsystem for Linux)
- Need to capture the Windows host screen
- Working on high-DPI displays (2560x1600, 4K, etc.)

## Quick Start

```bash
# Capture screenshot and save to workspace
python3 scripts/screenshot.py

# Or let the skill handle it
# Just say: "screenshot" or "capture my screen"
```

## How It Works

This skill uses PowerShell + .NET Framework (built into Windows) to capture the screen:

1. **DPI Awareness**: Calls `SetProcessDPIAware()` to detect actual screen resolution
2. **Graphics.CopyFromScreen**: Captures the entire screen to a Bitmap
3. **PNG Output**: Saves as compressed PNG for easy sharing

## Technical Details

### Supported Environments
- ✅ WSL2 with Windows 10/11
- ✅ High-DPI displays (retina/4K)
- ✅ Multi-monitor setups (captures primary screen)

### Limitations
- ❌ Native Linux (not WSL) - use `scrot` or `grim` instead
- ❌ macOS - use `peekaboo` skill instead
- ❌ Captures primary screen only (not all monitors)

## Resources

### scripts/
- `screenshot.py` - Main screenshot capture script

## Example Usage

**User**: "Can you take a screenshot?"

**Agent**:
1. Detect WSL2 environment
2. Run `scripts/screenshot.py`
3. Save to workspace as PNG
4. Send via message tool

Output: Full 2560x1600 screenshot (or actual resolution)
