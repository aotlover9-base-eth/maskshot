"""Command-line interface for MaskShot."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional
import click
from PIL import Image, ImageDraw, ImageFont
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .clipboard import ClipboardManager
from .detector import SecretDetector, DEFAULT_RULES
from .ocr import OCRProcessor
from .redactor import ImageRedactor, RedactionStyle

console = Console()


def get_preferred_font(size: int = 16) -> ImageFont.ImageFont:
    """Find and load a clean system monospaced font if available."""
    candidates = [
        "/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Regular.ttf",
        "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/home/aotlover9/.local/share/fonts/JetBrainsMono/JetBrainsMonoNerdFont-Regular.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


def send_desktop_notification(title: str, message: str, urgency: str = "normal") -> None:
    """Send a native Linux desktop notification using notify-send if available."""
    if shutil.which("notify-send"):
        try:
            subprocess.run(
                ["notify-send", "-u", urgency, "-a", "MaskShot", title, message],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx: click.Context) -> None:
    """MaskShot: Blazing fast, 100% offline screenshot & clipboard secret sanitizer."""
    if ctx.invoked_subcommand is None:
        console.print(
            Panel.fit(
                "[bold cyan]🛡️ MaskShot[/bold cyan] - [dim]Screenshot & Clipboard Secret Sanitizer[/dim]\n\n"
                "[bold]Quick Commands:[/bold]\n"
                "  [green]maskshot clip[/green]                 Sanitize current clipboard image\n"
                "  [green]maskshot sanitize <file>[/green]      Sanitize an image file\n"
                "  [green]maskshot watch[/green]                Watch screenshot folder in real-time\n"
                "  [green]maskshot rules[/green]                List all detectable secret types\n"
                "  [green]maskshot demo[/green]                 Generate test before/after demo image\n\n"
                "Run [dim]maskshot --help[/dim] for full options.",
                border_style="cyan",
            )
        )


@main.command(name="clip")
@click.option(
    "-s",
    "--style",
    type=click.Choice(["blur", "pixelate", "blackout", "badge"], case_sensitive=False),
    default="blur",
    help="Redaction visual style.",
)
@click.option("--badge", is_flag=True, help="Include secret type badge on blackout masks.")
@click.option("--padding", type=int, default=5, help="Padding around detected secrets (px).")
def clip_command(style: RedactionStyle, badge: bool, padding: int) -> None:
    """Grab image from clipboard, redact sensitive secrets, and paste it back."""
    cb = ClipboardManager()

    if not cb.has_image():
        console.print("[yellow]⚠️  No image found in clipboard![/yellow] Copy a screenshot and run again.")
        send_desktop_notification("MaskShot Warning", "No image currently in clipboard.", urgency="low")
        return

    console.print("[dim]Reading clipboard image...[/dim]")
    start_time = time.perf_counter()
    image = cb.get_image()

    if image is None:
        console.print("[red]❌ Failed to read image from clipboard.[/red]")
        return

    detector = SecretDetector()
    ocr = OCRProcessor(detector=detector)
    redactor = ImageRedactor(style=style)

    with console.status("[bold green]Scanning image for secrets (local OCR)...[/bold green]"):
        detected_boxes = ocr.process_image(image, padding=padding)

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    if not detected_boxes:
        console.print(f"[bold green]✨ Clean![/bold green] No sensitive secrets detected ({elapsed_ms}ms).")
        send_desktop_notification("MaskShot: Clean", f"No secrets found in screenshot ({elapsed_ms}ms).")
        return

    # Redact
    redacted_image = redactor.redact(image, detected_boxes, style=style, add_badge=badge)
    success = cb.set_image(redacted_image)

    # Show summary table
    table = Table(title=f"🛡️ Redacted {len(detected_boxes)} Secrets in {elapsed_ms}ms", border_style="cyan")
    table.add_column("Type", style="bold red")
    table.add_column("Masked Preview", style="dim yellow")
    table.add_column("Bounding Box", style="dim")

    for item in detected_boxes:
        val = item.match.value
        masked_preview = val[:4] + "*" * min(12, max(4, len(val) - 6)) + val[-2:] if len(val) > 8 else "****"
        box_str = f"({item.box.left}, {item.box.top}, {item.box.width}x{item.box.height})"
        table.add_row(item.match.secret_type, masked_preview, box_str)

    console.print(table)

    if success:
        console.print(f"[bold green]✅ Sanitized image copied back to clipboard![/bold green] Ready to paste.")
        types_summary = ", ".join(sorted({b.match.secret_type for b in detected_boxes}))
        send_desktop_notification(
            "MaskShot: Sanitized",
            f"Redacted {len(detected_boxes)} secret(s): {types_summary} in {elapsed_ms}ms.",
        )
    else:
        console.print("[red]❌ Failed to update clipboard.[/red]")


@main.command(name="sanitize")
@click.argument("input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-o", "--output", "output_path", type=click.Path(path_type=Path), default=None, help="Output image path.")
@click.option(
    "-s",
    "--style",
    type=click.Choice(["blur", "pixelate", "blackout", "badge"], case_sensitive=False),
    default="blur",
    help="Redaction visual style.",
)
@click.option("--badge", is_flag=True, help="Include secret type badge on blackout masks.")
@click.option("--padding", type=int, default=5, help="Padding around detected secrets (px).")
@click.option("--show", is_flag=True, help="Open image in default viewer after saving.")
def sanitize_command(
    input_path: Path,
    output_path: Optional[Path],
    style: RedactionStyle,
    badge: bool,
    padding: int,
    show: bool,
) -> None:
    """Sanitize an image file by redacting all sensitive secrets."""
    start_time = time.perf_counter()
    image = Image.open(input_path)

    detector = SecretDetector()
    ocr = OCRProcessor(detector=detector)
    redactor = ImageRedactor(style=style)

    with console.status(f"[bold green]Scanning {input_path.name}...[/bold green]"):
        detected_boxes = ocr.process_image(image, padding=padding)

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    if not output_path:
        output_path = input_path.parent / f"clean_{input_path.name}"

    if not detected_boxes:
        console.print(f"[bold green]✨ Clean![/bold green] No sensitive secrets detected in {input_path.name}.")
        image.save(output_path)
        console.print(f"Saved copy to: [cyan]{output_path}[/cyan]")
        return

    redacted_image = redactor.redact(image, detected_boxes, style=style, add_badge=badge)
    redacted_image.save(output_path)

    table = Table(title=f"🛡️ Redacted {len(detected_boxes)} Secrets in {elapsed_ms}ms", border_style="cyan")
    table.add_column("Type", style="bold red")
    table.add_column("Masked Preview", style="dim yellow")
    table.add_column("Bounding Box", style="dim")

    for item in detected_boxes:
        val = item.match.value
        masked_preview = val[:4] + "*" * min(12, max(4, len(val) - 6)) + val[-2:] if len(val) > 8 else "****"
        box_str = f"({item.box.left}, {item.box.top}, {item.box.width}x{item.box.height})"
        table.add_row(item.match.secret_type, masked_preview, box_str)

    console.print(table)
    console.print(f"[bold green]✅ Sanitized image saved to:[/bold green] [cyan]{output_path}[/cyan]")

    if show and shutil.which("xdg-open"):
        subprocess.run(["xdg-open", str(output_path)])


@main.command(name="rules")
def rules_command() -> None:
    """List all supported secret detection rules."""
    table = Table(title="🛡️ MaskShot Detection Rules", border_style="cyan")
    table.add_column("Category / Rule", style="bold green")
    table.add_column("Description", style="white")

    for rule in DEFAULT_RULES:
        table.add_row(rule.name, rule.description)

    console.print(table)


@main.command(name="demo")
@click.option("-o", "--output", type=click.Path(path_type=Path), default=Path("maskshot_demo.png"), help="Output path.")
@click.option(
    "-s",
    "--style",
    type=click.Choice(["blur", "pixelate", "blackout", "badge"], case_sensitive=False),
    default="blur",
    help="Redaction visual style.",
)
def demo_command(output: Path, style: RedactionStyle) -> None:
    """Generate a synthetic test card image with leaked secrets and redact it."""
    console.print("[dim]Generating synthetic test card image with clean TrueType font...[/dim]")

    font = get_preferred_font(size=18)
    title_font = get_preferred_font(size=18)

    w, h = 1000, 560
    img = Image.new("RGB", (w, h), color=(24, 24, 27))  # Dark modern zinc background
    draw = ImageDraw.Draw(img)

    # Window header bar
    draw.rectangle([0, 0, w, 44], fill=(39, 39, 42))
    draw.ellipse([16, 15, 28, 27], fill=(239, 68, 68))
    draw.ellipse([36, 15, 48, 27], fill=(245, 158, 11))
    draw.ellipse([56, 15, 68, 27], fill=(16, 185, 129))

    draw.text((90, 13), "production.env — Production Environment Config", fill=(212, 212, 216), font=title_font)

    lines = [
        ("# ⚠️ CONFIDENTIAL - DO NOT SHARE PUBLICLY", (113, 113, 122)),
        ("", (255, 255, 255)),
        ("OPENAI_API_KEY = \"sk-proj-9kL82mA918bCdf481ZaaqLx928174ka8\"", (244, 244, 245)),
        ("GITHUB_TOKEN   = \"ghp_182948194819481948194819481948194819\"", (244, 244, 245)),
        ("AWS_ACCESS_KEY = \"AKIAIOSFODNN7EXAMPLE\"", (244, 244, 245)),
        ("DATABASE_URL   = \"postgres://admin:SuperSecret99@192.168.1.155:5432/db\"", (244, 244, 245)),
        ("ADMIN_EMAIL    = \"security@antigravity.internal\"", (244, 244, 245)),
        ("SUPPORT_MOBILE = \"+91 9876543210\"", (244, 244, 245)),
        ("", (255, 255, 255)),
        ("def deploy():", (96, 165, 250)),
        ("    connect_vault(token=GITHUB_TOKEN)", (212, 212, 216)),
    ]

    y = 70
    for text, color in lines:
        draw.text((36, y), text, fill=color, font=font)
        y += 36

    # Run OCR and redaction
    ocr = OCRProcessor()
    redactor = ImageRedactor(style=style)

    detected = ocr.process_image(img, padding=5)
    redacted = redactor.redact(img, detected, style=style)

    # Combine into side-by-side comparison
    comp_w = w * 2 + 30
    comp_h = h + 60
    comparison = Image.new("RGB", (comp_w, comp_h), color=(15, 15, 18))
    comp_draw = ImageDraw.Draw(comparison)

    comp_draw.text((36, 18), "ORIGINAL (LEAKED SECRETS ⚠️)", fill=(248, 113, 113), font=title_font)
    comp_draw.text((w + 50, 18), f"MASKSHOT SANITIZED ({style.upper()} 🛡️)", fill=(52, 211, 153), font=title_font)

    comparison.paste(img, (20, 50))
    comparison.paste(redacted, (w + 30, 50))

    comparison.save(output)
    console.print(f"[bold green]✅ Demo card created successfully:[/bold green] [cyan]{output}[/cyan]")
    console.print(f"Redacted {len(detected)} secrets automatically.")


@main.command(name="watch")
@click.argument("directory", type=click.Path(exists=True, file_okay=False, path_type=Path), default=None, required=False)
@click.option(
    "-s",
    "--style",
    type=click.Choice(["blur", "pixelate", "blackout", "badge"], case_sensitive=False),
    default="blur",
    help="Redaction visual style.",
)
def watch_command(directory: Optional[Path], style: RedactionStyle) -> None:
    """Watch screenshot folder and automatically sanitize new images."""
    from .watcher import start_directory_watcher

    watch_path = directory
    if not watch_path:
        home = Path.home()
        candidates = [
            home / "Pictures" / "Screenshots",
            home / "Pictures",
            home / "Desktop",
        ]
        for c in candidates:
            if c.exists() and c.is_dir():
                watch_path = c
                break
        if not watch_path:
            watch_path = home / "Pictures"

    console.print(f"[bold cyan]👀 MaskShot Watcher active on:[/bold cyan] [green]{watch_path}[/green]")
    console.print("New screenshots will be automatically detected, scanned, and sanitized.")
    console.print("Press [dim]Ctrl+C[/dim] to stop.")

    def on_redacted_callback(clean_path: str, count: int) -> None:
        console.print(f"[bold green]🛡️ Sanitized:[/bold green] {Path(clean_path).name} ([red]{count} secrets redacted[/red])")
        send_desktop_notification("MaskShot Watcher", f"Sanitized {Path(clean_path).name}: {count} secrets redacted.")

    observer = start_directory_watcher(watch_path, style=style, on_redacted=on_redacted_callback)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        console.print("\n[yellow]Watcher stopped.[/yellow]")
    observer.join()
