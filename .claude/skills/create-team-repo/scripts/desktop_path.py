#!/usr/bin/env python3
"""Print the real Desktop folder of this computer.

The Desktop is not always ~/Desktop:
- Windows often moves it into OneDrive (OneDrive\\Desktop, or OneDrive\\Escritorio in
  Spanish). The system knows the real location: ask it (SHGetKnownFolderPath).
- Linux uses a localized name (Escritorio) recorded by xdg-user-dirs.
- macOS always uses ~/Desktop on disk, even when Finder shows "Escritorio".

Standard library only.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path


def windows_desktop():
    import ctypes
    from ctypes import wintypes

    class GUID(ctypes.Structure):
        _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD),
                    ("Data3", wintypes.WORD), ("Data4", wintypes.BYTE * 8)]

    # FOLDERID_Desktop {B4BFCC3A-DB2C-424C-B029-7FE99A87C641}
    folder_id = GUID(0xB4BFCC3A, 0xDB2C, 0x424C, (wintypes.BYTE * 8)(0xB0, 0x29, 0x7F, 0xE9, 0x9A, 0x87, 0xC6, 0x41))
    path_ptr = ctypes.c_wchar_p()
    result = ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(folder_id), 0, None, ctypes.byref(path_ptr))
    if result != 0:
        return None
    path = path_ptr.value
    ctypes.windll.ole32.CoTaskMemFree(path_ptr)
    return path


def linux_desktop():
    try:
        out = subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True, text=True, timeout=5).stdout.strip()
        return out or None
    except (OSError, subprocess.SubprocessError):
        return None


def main():
    system = platform.system()
    path = None
    if system == "Windows":
        path = windows_desktop()
    elif system == "Linux":
        path = linux_desktop()
    path = Path(path) if path else Path.home() / "Desktop"
    if not path.is_dir():
        path = Path.home()
    print(os.fspath(path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
