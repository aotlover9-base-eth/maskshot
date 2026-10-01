"""Clipboard integration module for Wayland and X11 on Linux."""

from __future__ import annotations

import io
import os
import shutil
import subprocess
from typing import Optional
from PIL import Image


class ClipboardManager:
    """Handles reading and writing images to/from system clipboard."""

    def __init__(self):
        self.is_wayland = bool(os.environ.get("WAYLAND_DISPLAY") or os.environ.get("XDG_SESSION_TYPE") == "wayland")
        self.has_wl = bool(shutil.which("wl-paste") and shutil.which("wl-copy"))
        self.has_xclip = bool(shutil.which("xclip"))

    def has_image(self) -> bool:
        """Check if clipboard currently contains an image."""
        if self.is_wayland and self.has_wl:
            try:
                res = subprocess.run(["wl-paste", "--list-types"], capture_output=True, text=True, check=True)
                return any(t.startswith("image/") for t in res.stdout.splitlines())
            except Exception:
                return False
        elif self.has_xclip:
            try:
                res = subprocess.run(
                    ["xclip", "-selection", "clipboard", "-t", "TARGETS", "-o"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                return any("image" in t for t in res.stdout.splitlines())
            except Exception:
                return False
        return False

    def get_image(self) -> Optional[Image.Image]:
        """Fetch image currently in clipboard."""
        if self.is_wayland and self.has_wl:
            try:
                # Try image/png then fallback to any image type
                res = subprocess.run(["wl-paste", "--type", "image/png"], capture_output=True, check=True)
                return Image.open(io.BytesIO(res.stdout))
            except Exception:
                pass

        if self.has_xclip:
            try:
                res = subprocess.run(
                    ["xclip", "-selection", "clipboard", "-t", "image/png", "-o"],
                    capture_output=True,
                    check=True,
                )
                return Image.open(io.BytesIO(res.stdout))
            except Exception:
                pass

        return None

    def set_image(self, image: Image.Image) -> bool:
        """Write an image to clipboard."""
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        raw_bytes = buffer.getvalue()

        if self.is_wayland and self.has_wl:
            try:
                proc = subprocess.Popen(["wl-copy", "--type", "image/png"], stdin=subprocess.PIPE)
                proc.communicate(input=raw_bytes)
                return proc.returncode == 0
            except Exception:
                pass

        if self.has_xclip:
            try:
                proc = subprocess.Popen(
                    ["xclip", "-selection", "clipboard", "-t", "image/png", "-i"],
                    stdin=subprocess.PIPE,
                )
                proc.communicate(input=raw_bytes)
                return proc.returncode == 0
            except Exception:
                pass

        return False
