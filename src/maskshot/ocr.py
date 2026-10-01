"""OCR processing module to extract text and compute bounding boxes for secrets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple
from PIL import Image
import pytesseract
from pytesseract import Output

from .detector import SecretDetector, SecretMatch


@dataclass
class BoundingBox:
    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height

    def expand(self, padding_x: int = 4, padding_y: int = 4, max_width: int = 999999, max_height: int = 999999) -> BoundingBox:
        """Add safety padding around bounding box to prevent partial text bleed."""
        new_left = max(0, self.left - padding_x)
        new_top = max(0, self.top - padding_y)
        new_right = min(max_width, self.right + padding_x)
        new_bottom = min(max_height, self.bottom + padding_y)
        return BoundingBox(
            left=new_left,
            top=new_top,
            width=new_right - new_left,
            height=new_bottom - new_top,
        )

    def intersects(self, other: BoundingBox) -> bool:
        """Check if this box overlaps or is adjacent to another box."""
        return not (
            self.right < other.left
            or self.left > other.right
            or self.bottom < other.top
            or self.top > other.bottom
        )

    def merge(self, other: BoundingBox) -> BoundingBox:
        """Merge two overlapping bounding boxes."""
        new_left = min(self.left, other.left)
        new_top = min(self.top, other.top)
        new_right = max(self.right, other.right)
        new_bottom = max(self.bottom, other.bottom)
        return BoundingBox(
            left=new_left,
            top=new_top,
            width=new_right - new_left,
            height=new_bottom - new_top,
        )


@dataclass
class DetectedSecretBox:
    match: SecretMatch
    box: BoundingBox


def merge_overlapping_boxes(boxes: List[DetectedSecretBox]) -> List[DetectedSecretBox]:
    """Merge overlapping or nested bounding boxes into consolidated boxes."""
    if not boxes:
        return []

    # Sort boxes from left to right
    sorted_boxes = sorted(boxes, key=lambda b: (b.box.top, b.box.left))
    merged: List[DetectedSecretBox] = []

    for item in sorted_boxes:
        absorbed = False
        for i, existing in enumerate(merged):
            if existing.box.intersects(item.box):
                # Merge boxes
                new_box = existing.box.merge(item.box)
                # Keep the more specific or priority secret type
                priority_type = (
                    item.match.secret_type
                    if "Key" in item.match.secret_type or "Token" in item.match.secret_type
                    else existing.match.secret_type
                )
                merged[i] = DetectedSecretBox(
                    match=SecretMatch(
                        secret_type=priority_type,
                        value=existing.match.value,
                        start=existing.match.start,
                        end=max(existing.match.end, item.match.end),
                        description=existing.match.description,
                    ),
                    box=new_box,
                )
                absorbed = True
                break

        if not absorbed:
            merged.append(item)

    return merged


class OCRProcessor:
    """Processes images with Tesseract and finds bounding boxes of sensitive matches."""

    def __init__(self, detector: SecretDetector | None = None):
        self.detector = detector or SecretDetector()

    def process_image(self, image: Image.Image, padding: int = 4) -> List[DetectedSecretBox]:
        """Runs OCR on image, extracts lines, matches secrets, and computes bounding boxes."""
        if image.mode != "RGB":
            processed_img = image.convert("RGB")
        else:
            processed_img = image

        img_w, img_h = processed_img.size

        # Extract OCR data dictionary
        ocr_data = pytesseract.image_to_data(processed_img, output_type=Output.DICT)
        num_items = len(ocr_data["text"])

        # Group words by (block_num, par_num, line_num)
        lines_map: dict[Tuple[int, int, int], list[dict]] = {}
        for i in range(num_items):
            text = ocr_data["text"][i].strip()
            if not text:
                continue

            key = (ocr_data["block_num"][i], ocr_data["par_num"][i], ocr_data["line_num"][i])
            if key not in lines_map:
                lines_map[key] = []

            lines_map[key].append({
                "text": text,
                "left": ocr_data["left"][i],
                "top": ocr_data["top"][i],
                "width": ocr_data["width"][i],
                "height": ocr_data["height"][i],
                "conf": ocr_data["conf"][i],
            })

        raw_detected: List[DetectedSecretBox] = []

        # Analyze each line
        for words in lines_map.values():
            line_str = ""
            word_spans: list[tuple[int, int, dict]] = []

            for word_info in words:
                w_text = word_info["text"]
                if line_str and not line_str.endswith(" "):
                    line_str += " "
                start_idx = len(line_str)
                line_str += w_text
                end_idx = len(line_str)
                word_spans.append((start_idx, end_idx, word_info))

            matches = self.detector.scan_text(line_str)
            for match in matches:
                overlapping_words = [
                    w for (start, end, w) in word_spans
                    if not (end <= match.start or start >= match.end)
                ]

                if not overlapping_words:
                    continue

                min_left = min(w["left"] for w in overlapping_words)
                min_top = min(w["top"] for w in overlapping_words)
                max_right = max(w["left"] + w["width"] for w in overlapping_words)
                max_bottom = max(w["top"] + w["height"] for w in overlapping_words)

                raw_box = BoundingBox(
                    left=min_left,
                    top=min_top,
                    width=max_right - min_left,
                    height=max_bottom - min_top,
                )
                padded_box = raw_box.expand(padding_x=padding, padding_y=padding, max_width=img_w, max_height=img_h)
                raw_detected.append(DetectedSecretBox(match=match, box=padded_box))

        return merge_overlapping_boxes(raw_detected)
