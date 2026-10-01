<div align="center">

# 🛡️ MaskShot

### *Auto-blur API keys, passwords, and emails in screenshots before posting.*

Takes whatever is in your clipboard, blurs out leaked secrets, and puts it right back in **< 300ms**.

[![Day 2 / 100](https://img.shields.io/badge/100_Days_Challenge-Day_002-blue?style=for-the-badge)](https://github.com/aotlover9-base-eth/100-days-100-problems-100-solutions)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Tesseract OCR](https://img.shields.io/badge/OCR-Tesseract_5.5-green?style=for-the-badge)](https://github.com/tesseract-ocr/tesseract)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

<br/>

![MaskShot Demo](maskshot_demo.png)

</div>

---

## ⚡ The Problem

You take a screenshot of your terminal or code editor to ask a question on Twitter, Discord, or GitHub. 
Without realizing it, your **OpenAI API key**, **database password**, or **phone number** is visible in the corner. 

Sending screenshots to cloud un-blur / redaction tools is risky because your secrets leave your computer.

---

## 💡 The Solution: MaskShot

**MaskShot is 100% offline.** It scans images on your local machine using local OCR (Tesseract), finds sensitive patterns, and masks them immediately.

* **📋 Instant Clipboard Sanitizer (`maskshot clip`):** Copy any screenshot, run `maskshot clip`, and paste. Done.
* **🔒 100% Offline & Free ($0):** No cloud APIs, no subscriptions. Everything runs locally in memory.
* **🎨 3 Mask Styles:** Gaussian Blur, Retro Pixelate, or Blackout Boxes with labels.
* **👀 Background Watcher:** Auto-scans and blurs new screenshots saved in your folder.

---

## 🚀 2-Minute Quickstart

### 1. Install System OCR (Tesseract)
```bash
# Ubuntu / Debian
sudo apt install tesseract-ocr

# Arch / CachyOS / Manjaro
sudo pacman -S tesseract tesseract-data-eng

# Fedora
sudo dnf install tesseract
```

### 2. Install MaskShot
```bash
pip install git+https://github.com/aotlover9-base-eth/maskshot.git
```
*(Or if you use `uv`: `uv tool install git+https://github.com/aotlover9-base-eth/maskshot.git`)*

---

## 🛠️ How to Use

### 1. The Fastest Way: Sanitize Clipboard
Take a screenshot as usual (`PrintScreen` or your shortcut), then run:
```bash
maskshot clip
```
Now press `Ctrl + V` anywhere — all secrets are blurred!

### 2. Sanitize an Image File
```bash
# Standard Blur
maskshot sanitize screenshot.png -o clean.png

# Retro Pixelate
maskshot sanitize screenshot.png -s pixelate -o clean.png

# Blackout with Category Labels
maskshot sanitize screenshot.png -s blackout --badge -o clean.png
```

### 3. Test on a Sample Demo Image
Generate a test screenshot and see the before/after:
```bash
maskshot demo -o test.png
```

---

## 🧠 How Does MaskShot Know What to Mask?

All rules are defined in [`src/maskshot/detector.py`](src/maskshot/detector.py). 

MaskShot uses high-accuracy **regular expressions (Regex)** designed specifically for credentials and PII:

| Type | How It Detects | Examples |
|:---|:---|:---|
| **AI Keys** | `sk-proj-...` or `sk-ant-...` followed by 20+ characters | OpenAI, Anthropic Claude |
| **Cloud Tokens** | `ghp_...`, `AKIA...`, `AIza...`, `hf_...` | GitHub PAT, AWS, Google Cloud, HuggingFace |
| **Databases** | `postgres://`, `mongodb://`, `mysql://`, `redis://` | Database URLs with passwords |
| **Auth** | `xoxb-...`, `sk_live_...`, `eyJ...` | Slack tokens, Stripe keys, JWTs, Private keys |
| **PII** | Email pattern (`user@domain.com`), 10-digit phone numbers (`+91...`), IPv4 addresses | Emails, Phone numbers, Server IPs |
| **Config** | `password = "..."` or `SECRET_KEY = "..."` | Any password assigned in code or `.env` files |

To see the live rules in your terminal:
```bash
maskshot rules
```

---

## ⌨️ Shortcut Tip (1-Tap Sanitize)

Set `maskshot clip` as a global hotkey (e.g. `Super + Shift + C`):
1. Open **Settings -> Keyboard -> Keyboard Shortcuts**.
2. Add a new custom shortcut with command: `maskshot clip`.
3. Set shortcut to **`Super + Shift + C`**.

Now anytime you capture a screenshot, tap `Super + Shift + C` to sanitize it in 1 second!

---

## 📜 License
MIT License © 2026 Nikhil Gupta. Built as Day 2 of the **100 Days, 100 Problems, 100 Solutions** challenge.
