"""Detector module for identifying sensitive secrets, API keys, credentials, and PII."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Pattern
import yaml


@dataclass
class SecretMatch:
    secret_type: str
    value: str
    start: int
    end: int
    description: str


@dataclass
class DetectionRule:
    name: str
    pattern: Pattern[str]
    description: str
    extract_group: int = 0


DEFAULT_RULES: List[DetectionRule] = [
    # API Keys & Cloud Providers
    DetectionRule(
        name="OpenAI API Key",
        pattern=re.compile(r"\b(sk[-_](?:proj|admin)[-_][a-zA-Z0-9_\-]{20,}|sk-[a-zA-Z0-9]{20,})\b"),
        description="OpenAI secret key or project key",
        extract_group=1,
    ),
    DetectionRule(
        name="Anthropic API Key",
        pattern=re.compile(r"\b(sk-ant-(?:api\d+-)?[\w\-]{20,})\b"),
        description="Anthropic Claude API key",
        extract_group=1,
    ),
    DetectionRule(
        name="GitHub Personal Access Token",
        pattern=re.compile(r"\b(gh[pousr][-_][A-Za-z0-9_]{36,}|github[-_]pat[-_][A-Za-z0-9_]{80,})\b"),
        description="GitHub personal access or OAuth token",
        extract_group=1,
    ),
    DetectionRule(
        name="AWS Access Key ID",
        pattern=re.compile(r"\b((?:AKIA|ASIA|ABIA|ACCA)[0-9A-Z]{16})\b"),
        description="Amazon Web Services access key identifier",
        extract_group=1,
    ),
    DetectionRule(
        name="Google Cloud API Key",
        pattern=re.compile(r"\b(AIza[0-9A-Za-z\-_]{35})\b"),
        description="Google Cloud / Firebase API key",
        extract_group=1,
    ),
    DetectionRule(
        name="Stripe Secret / Restricted Key",
        pattern=re.compile(r"\b([rs]k_(?:live|test)_[0-9a-zA-Z]{24,})\b"),
        description="Stripe secret or live API key",
        extract_group=1,
    ),
    DetectionRule(
        name="Slack Token",
        pattern=re.compile(r"\b(xox[baprs]-[0-9a-zA-Z]{10,48})\b"),
        description="Slack bot or user token",
        extract_group=1,
    ),
    DetectionRule(
        name="HuggingFace Token",
        pattern=re.compile(r"\b(hf_[a-zA-Z0-9]{34,})\b"),
        description="HuggingFace user access token",
        extract_group=1,
    ),
    DetectionRule(
        name="JWT Token",
        pattern=re.compile(r"\b(eyJ[a-zA-Z0-9_\-]{10,}\.eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]+)\b"),
        description="JSON Web Token (JWT)",
        extract_group=1,
    ),
    DetectionRule(
        name="Private Key Header",
        pattern=re.compile(r"(-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----)"),
        description="SSH or TLS private key header",
        extract_group=1,
    ),

    # Database URLs
    DetectionRule(
        name="Database Connection String",
        pattern=re.compile(r"\b((?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis):\s*\/\/[^\s\"'<>]+)\b"),
        description="Database connection URI with credentials",
        extract_group=1,
    ),

    # Generic Config / Password Assignment
    DetectionRule(
        name="Password / Secret Assignment",
        pattern=re.compile(
            r"(?i)\b(?:password|passwd|secret|api_key|apikey|access_token|auth_token|client_secret)\s*[:=]\s*['\"]?([^\s'\"`]{6,})['\"]?"
        ),
        description="Plaintext password or token assignment in code/env",
        extract_group=1,
    ),

    # PII (Emails, Phone Numbers, IPs)
    DetectionRule(
        name="Email Address",
        pattern=re.compile(r"\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\b"),
        description="Personal or corporate email address",
        extract_group=1,
    ),
    DetectionRule(
        name="Phone Number (IN/Intl)",
        pattern=re.compile(
            r"(?<![a-zA-Z0-9_\-\.])(?:\+?91[\s-]?)?([6-9]\d{9})(?![a-zA-Z0-9_\-\.])|(?<![a-zA-Z0-9_\-\.])(?:\+?1[\s-]?)?(\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})(?![a-zA-Z0-9_\-\.])"
        ),
        description="Phone number",
        extract_group=0,
    ),
    DetectionRule(
        name="IPv4 Address",
        pattern=re.compile(r"\b((?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))\b"),
        description="IPv4 network address",
        extract_group=1,
    ),
]


class SecretDetector:
    """Detects secrets in text lines or blocks using predefined and custom rules."""

    def __init__(self, custom_rules: Optional[List[DetectionRule]] = None, excluded_ips: Optional[set[str]] = None):
        self.rules = list(DEFAULT_RULES)
        if custom_rules:
            self.rules.extend(custom_rules)
        self.excluded_ips = excluded_ips or {"127.0.0.1", "0.0.0.0", "255.255.255.255", "8.8.8.8", "1.1.1.1"}
        self._load_user_config()

    def _load_user_config(self) -> None:
        """Load optional user config from ~/.config/maskshot/config.yaml or .maskshot.yaml"""
        config_paths = [
            Path.home() / ".config" / "maskshot" / "config.yaml",
            Path.cwd() / ".maskshot.yaml",
        ]
        for p in config_paths:
            if p.exists() and p.is_file():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f) or {}

                    # Custom literal keywords
                    for kw in data.get("custom_keywords", []):
                        if isinstance(kw, str) and kw.strip():
                            self.add_keyword_rule(kw.strip())

                    # Custom regexes
                    for item in data.get("custom_rules", []):
                        if isinstance(item, dict) and "pattern" in item:
                            name = item.get("name", "Custom Rule")
                            pat = item["pattern"]
                            desc = item.get("description", "User custom rule")
                            group = item.get("extract_group", 0)
                            self.rules.append(
                                DetectionRule(
                                    name=name,
                                    pattern=re.compile(pat),
                                    description=desc,
                                    extract_group=group,
                                )
                            )
                except Exception:
                    pass

    def add_keyword_rule(self, keyword: str, name: Optional[str] = None) -> None:
        """Add a specific literal keyword (e.g. your username or internal company name) to redact."""
        escaped = re.escape(keyword)
        self.rules.append(
            DetectionRule(
                name=name or f"Keyword: {keyword}",
                pattern=re.compile(rf"\b({escaped})\b", re.IGNORECASE),
                description=f"User-specified keyword: {keyword}",
                extract_group=1,
            )
        )

    def scan_text(self, text: str) -> List[SecretMatch]:
        """Scan a given string and return all identified secret matches."""
        matches: List[SecretMatch] = []
        for rule in self.rules:
            for match in rule.pattern.finditer(text):
                try:
                    val = match.group(rule.extract_group)
                    start = match.start(rule.extract_group)
                    end = match.end(rule.extract_group)
                except (IndexError, ValueError):
                    val = match.group(0)
                    start = match.start(0)
                    end = match.end(0)

                if not val:
                    continue

                if rule.name == "IPv4 Address" and val in self.excluded_ips:
                    continue

                matches.append(
                    SecretMatch(
                        secret_type=rule.name,
                        value=val,
                        start=start,
                        end=end,
                        description=rule.description,
                    )
                )
        return matches
