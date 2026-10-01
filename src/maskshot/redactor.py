"""Redaction engine to apply visual masks (blur, pixelate, blackout) on target boxes."""

from __future__ import annotations

from typing import List, Literal
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .ocr import DetectedSecretBox

RedactionStyle = Literal["blur", "pixelate", "blackout", "badge"]


class ImageRedactor:
    """Applies privacy masks to detected bounding boxes."""

    def __init__(self, style: RedactionStyle = "blur", blur_radius: int = 14, pixel_size: int = 8):
        self.style = style
        self.blur_radius = blur_radius
        self.pixel_size = pixel_size

    def redact(
        self,
        image: Image.Image,
        boxes: List[DetectedSecretBox],
        style: RedactionStyle | None = None,
        add_badge: bool = False,
    ) -> Image.Image:
        """Returns a copy of the image with all specified bounding boxes redacted."""
        active_style = style or self.style
        output_img = image.copy()

        # Handle different image modes
        if output_img.mode not in ("RGB", "RGBA"):
            output_img = output_img.convert("RGB")

        draw = ImageDraw.Draw(output_img)

        for secret in boxes:
            box = secret.box
            # Ensure box coordinates are valid within the image bounds
            x0 = max(0, box.left)
            y0 = max(0, box.top)
            x1 = min(output_img.width, box.right)
            y1 = min(output_img.height, box.bottom)

            if x1 <= x0 or y1 <= y0:
                continue

            crop_box = (x0, y0, x1, y1)
            region = output_img.crop(crop_box)

            if active_style == "blur":
                # Apply strong Gaussian blur
                blurred = region.filter(ImageFilter.GaussianBlur(radius=self.blur_radius))
                output_img.paste(blurred, crop_box)

            elif active_style == "pixelate":
                # Downscale then upscale with nearest neighbor
                w = max(1, (x1 - x0) // self.pixel_size)
                h = max(1, (y1 - y0) // self.pixel_size)
                small = region.resize((w, h), resample=Image.Resampling.BILINEAR)
                pixelated = small.resize((x1 - x0, y1 - y0), resample=Image.Resampling.NEAREST)
                output_img.paste(pixelated, crop_box)

            elif active_style == "blackout":
                # Solid dark rounded rectangle
                bg_color = (17, 24, 39) if output_img.mode == "RGB" else (17, 24, 39, 255)
                border_color = (55, 65, 81) if output_img.mode == "RGB" else (55, 65, 81, 255)
                radius = min(4, (y1 - y0) // 2)
                draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=bg_color, outline=border_color, width=1)

                if add_badge and (x1 - x0 > 40) and (y1 - y0 > 14):
                    label = f"[{secret.match.secret_type.upper()}]"
                    font = ImageFont.load_default()
                    text_color = (209, 213, 219)
                    draw.text((x0 + 4, y0 + max(1, (y1 - y0 - 10) // 2)), label, fill=text_color, font=font)

            elif active_style == "badge":
                # Blackout with clean badge label
                bg_color = (15, 23, 42)
                border_color = (239, 68, 68)  # Red outline indicating redacted secret
                radius = min(4, (y1 - y0) // 2)
                draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=bg_color, outline=border_color, width=1)

                label = f"REDACTED: {secret.match.secret_type}"
                font = ImageFont.load_default()
                text_color = (248, 113, 113)
                draw.text((x0 + 4, y0 + max(1, (y1 - y0 - 10) // 2)), label, fill=text_color, font=font)

        return output_img
