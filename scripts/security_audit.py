from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache"}

FORBIDDEN_MARKERS = (
    "TO" + "DO",
    "FIX" + "ME",
    "implement " + "later",
    "BEGIN " + "PRIVATE KEY",
)

SENSITIVE_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}


def main() -> None:
    violations: list[str] = []

    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in SKIP for part in path.parts):
            continue

        relative = path.relative_to(ROOT)
        if path.name == ".env" or path.name.startswith(".env."):
            violations.append(f"sensitive environment file tracked: {relative}")
            continue
        if path.suffix.lower() in SENSITIVE_SUFFIXES:
            violations.append(f"sensitive key material tracked: {relative}")
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        if path.name == "security_audit.py":
            continue

        lowered = text.lower()
        for marker in FORBIDDEN_MARKERS:
            if marker.lower() in lowered:
                violations.append(f"forbidden marker found in {relative}")
                break

    if violations:
        raise SystemExit("Security audit failed:
- " + "
- ".join(sorted(set(violations))))

    print("Security audit passed.")


if __name__ == "__main__":
    main()
