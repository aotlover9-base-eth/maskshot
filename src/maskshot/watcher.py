"""Filesystem and clipboard watcher module."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Callable, Optional
from PIL import Image
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
from watchdog.observers import Observer

from .ocr import OCRProcessor
from .redactor import ImageRedactor, RedactionStyle


class ScreenshotHandler(FileSystemEventHandler):
    """Watches a directory for new screenshots and auto-redacts them."""

    def __init__(
        self,
        ocr: OCRProcessor,
        redactor: ImageRedactor,
        output_dir: Optional[Path] = None,
        on_redacted: Optional[Callable[[str, int], None]] = None,
        style: RedactionStyle = "blur",
    ):
        super().__init__()
        self.ocr = ocr
        self.redactor = redactor
        self.output_dir = output_dir
        self.on_redacted = on_redacted
        self.style = style
        self.processed_files: set[str] = set()

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if file_path.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
            return

        # Wait briefly for writer to finish flushing to disk
        time.sleep(0.3)

        if str(file_path) in self.processed_files:
            return

        try:
            with Image.open(file_path) as img:
                detected = self.ocr.process_image(img)
                if not detected:
                    return

                redacted = self.redactor.redact(img, detected, style=self.style)

                if self.output_dir:
                    self.output_dir.mkdir(parents=True, exist_ok=True)
                    out_path = self.output_dir / f"clean_{file_path.name}"
                else:
                    out_path = file_path.parent / f"clean_{file_path.name}"

                redacted.save(out_path)
                self.processed_files.add(str(file_path))

                if self.on_redacted:
                    self.on_redacted(str(out_path), len(detected))

        except Exception:
            # File might be partially written or locked
            pass


def start_directory_watcher(
    watch_dir: Path,
    output_dir: Optional[Path] = None,
    style: RedactionStyle = "blur",
    on_redacted: Optional[Callable[[str, int], None]] = None,
) -> Observer:
    """Start watching a folder in the background."""
    ocr = OCRProcessor()
    redactor = ImageRedactor(style=style)
    handler = ScreenshotHandler(ocr, redactor, output_dir=output_dir, on_redacted=on_redacted, style=style)

    observer = Observer()
    observer.schedule(handler, str(watch_dir), recursive=False)
    observer.start()
    return observer
