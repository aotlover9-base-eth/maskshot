<div align="center">

# 🛡️ MaskShot

### *Blazing-fast, 100% offline screenshot & clipboard secret sanitizer.*

Auto-detect and redact leaked API keys, tokens, credentials, and personal data in your screenshots before posting to X, GitHub, or Discord.

[![Day 2 / 100](https://img.shields.io/badge/100_Days_Challenge-Day_002-blue?style=for-the-badge)](https://github.com/aotlover9-base-eth/100-days-100-problems-100-solutions)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Tesseract OCR](https://img.shields.io/badge/OCR-Tesseract_5.5-green?style=for-the-badge)](https://github.com/tesseract-ocr/tesseract)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

</div>

---

## 🎯 The Problem

Developers and creators take dozens of screenshots daily to share code errors, terminal output, or dashboard previews on Twitter/X, GitHub issues, and Discord. 

It is dangerously easy to accidentally leak:
- **API Keys:** `sk-proj-...`, `ghp_...`, `AKIA...`
- **Database URIs:** `postgres://user:password@...`
- **Private Info:** Corporate emails, phone numbers, server IP addresses

Cloud-based redaction tools defeat the purpose — sending your unredacted secrets over the internet to a third-party server is itself a security risk.

---

## 💡 The Solution

**MaskShot** runs **100% locally and offline**. It scans screenshots using local OCR (Tesseract 5.5) and applies intelligent regex pattern matching to detect and mask secrets in under **300ms**.

- ⚡ **Zero Cloud / $0 Cost:** Zero external API calls. Your images and tokens never leave your RAM.
- 📋 **One-Click Clipboard Sanitizer (`maskshot clip`):** Grab whatever screenshot is in your clipboard, redact all secrets, and paste it back immediately.
- 🎨 **Multiple Mask Styles:** Gaussian Blur, Retro Pixelation, or Solid Rounded Blackout with badges.
- 🔔 **Native Desktop Alerts:** Integrated with Linux desktop notifications (`notify-send`).
- 📁 **Folder Watcher (`maskshot watch`):** Monitors your screenshot folder and auto-sanitizes new screenshots silently in the background.

---

## 📸 Before & After

```
BEFORE (Leaked Credentials)                 AFTER (MaskShot Sanitized)
┌─────────────────────────────────┐         ┌─────────────────────────────────┐
│ OPENAI_KEY = "sk-proj-9kL82..." │  ───►   │ OPENAI_KEY = "██████████████"   │
│ DB_URL = "postgres://admin:..." │         │ DB_URL = "██████████████████"   │
│ EMAIL = "founder@company.io"    │         │ EMAIL = "███████████████████"   │
└─────────────────────────────────┘         └─────────────────────────────────┘
```

---

## 🚀 Quickstart & Installation

### 1. Prerequisites (Tesseract OCR)
MaskShot uses Tesseract OCR for local character recognition:

```bash
# Arch / Manjaro
sudo pacman -S tesseract tesseract-data-eng

# Ubuntu / Debian
sudo apt install tesseract-ocr tesseract-ocr-eng

# Fedora
sudo dnf install tesseract tesseract-langpack-eng
```

### 2. Install MaskShot

Using `uv` (recommended):
```bash
uv tool install git+https://github.com/aotlover9-base-eth/maskshot.git
```

Or via standard `pip`:
```bash
git clone https://github.com/aotlover9-base-eth/maskshot.git
cd maskshot
pip install -e .
```

---

## 🛠️ Usage

### 1. Sanitize Clipboard in 1 Second
Take a screenshot (e.g. using `Spectacle`, `Flameshot`, `Grim`, or GNOME screenshot shortcut), then simply run:

```bash
maskshot clip
```
*MaskShot immediately reads your clipboard, masks every detected secret, replaces the clipboard image, and pops up a desktop notification with the redacted count.*

### 2. Sanitize an Image File
```bash
# Default Gaussian blur
maskshot sanitize screenshot.png

# Custom output file
maskshot sanitize screenshot.png -o clean_screenshot.png

# Retro Pixelate style
maskshot sanitize screenshot.png -s pixelate

# Solid Blackout style with secret badges
maskshot sanitize screenshot.png -s blackout --badge
```

### 3. Background Watcher Mode
Automatically monitor your screenshot folder and sanitize every screenshot as soon as it's saved:

```bash
maskshot watch ~/Pictures/Screenshots
```

### 4. View All Detectable Secret Types
```bash
maskshot rules
```

### 5. Generate a Demo Card
Test MaskShot locally on a synthetic mock environment file:
```bash
maskshot demo -s blur -o demo.png
```

---

## 🔍 Supported Secret Types

| Category | Patterns Detected |
|:---|:---|
| **AI & LLM Keys** | OpenAI (`sk-proj-...`, `sk-...`), Anthropic Claude (`sk-ant-...`) |
| **Cloud & DevOps** | GitHub PAT (`ghp_...`, `github_pat_...`), AWS Access Keys (`AKIA...`), Google Cloud (`AIza...`), HuggingFace (`hf_...`) |
| **Auth & Security** | Slack Tokens (`xoxb-...`), Stripe Keys (`sk_live_...`), JWT Tokens (`eyJ...`), SSH/RSA Private Keys |
| **Databases** | Connection strings (`postgres://`, `mongodb://`, `mysql://`, `redis://`) |
| **PII & Network** | Email addresses, Phone numbers (International & Indian standard), IPv4 network addresses |
| **Config Secrets** | Environment variable password assignments (`password = "..."`, `SECRET_KEY = "..."`) |

---

## ⌨️ Pro-Tip: Hotkey Integration (Linux)

Bind `maskshot clip` to a global keyboard shortcut (like `Super + Shift + C` or `Ctrl + Alt + M`):
1. Go to your system **Settings -> Keyboard -> Custom Shortcuts**.
2. Add Command: `maskshot clip`
3. Set Shortcut: `Super + Shift + C`

Now, whenever you capture a screenshot, tap `Super + Shift + C` — your clipboard is instantly sanitized and ready to paste anywhere safely!

---

## 📜 License

MIT License © 2026 Nikhil Gupta ([@aotlover9-base-eth](https://github.com/aotlover9-base-eth)). Built as part of the **100 Days, 100 Problems, 100 Solutions** challenge.
