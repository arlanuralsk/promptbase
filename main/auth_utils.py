import re


def normalize_phone(value):
    raw = (value or "").strip()
    if not raw:
        return ""
    prefix = "+" if raw.startswith("+") else ""
    digits = re.sub(r"\D", "", raw)
    return f"{prefix}{digits}" if digits else ""


def looks_like_email(value):
    return "@" in (value or "")
