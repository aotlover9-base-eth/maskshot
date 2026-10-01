from PIL import Image
from maskshot.detector import SecretMatch
from maskshot.ocr import BoundingBox, DetectedSecretBox
from maskshot.redactor import ImageRedactor

def test_image_redactor_blur():
    img = Image.new("RGB", (200, 200), color=(255, 255, 255))
    redactor = ImageRedactor(style="blur")
    
    match = SecretMatch(
        secret_type="OpenAI API Key",
        value="sk-12345",
        start=0,
        end=8,
        description="test",
    )
    box = DetectedSecretBox(match=match, box=BoundingBox(left=20, top=20, width=100, height=30))
    
    redacted = redactor.redact(img, [box], style="blur")
    assert redacted.size == (200, 200)

def test_image_redactor_blackout():
    img = Image.new("RGB", (200, 200), color=(255, 255, 255))
    redactor = ImageRedactor(style="blackout")
    
    match = SecretMatch(
        secret_type="OpenAI API Key",
        value="sk-12345",
        start=0,
        end=8,
        description="test",
    )
    box = DetectedSecretBox(match=match, box=BoundingBox(left=20, top=20, width=100, height=30))
    
    redacted = redactor.redact(img, [box], style="blackout")
    # Pixel in the middle of the redacted region should no longer be white
    pixel = redacted.getpixel((50, 35))
    assert pixel != (255, 255, 255)
