"""Maintain audit data in the unified engineering guide without replacing its prose."""
from pathlib import Path
import json
import os
import re
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / 'docs/GUIA_MFC_STUDIO.md'


def replace_audit(text, name, report):
    if not re.fullmatch(r'[a-z0-9][a-z0-9._-]*', name):
        raise ValueError('Invalid audit identifier')
    start = f'<!-- audit:{name}:start -->'
    end = f'<!-- audit:{name}:end -->'
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f'Exactly one existing audit block is required: {name}')
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    return before + start + '\n```json\n' + payload + '\n```\n' + end + after


def write_audit(name, report, guide=GUIDE):
    guide = Path(guide)
    updated = replace_audit(guide.read_text(), name, report)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=guide.parent, suffix='.tmp', delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(updated)
    try:
        temporary.replace(guide)
    finally:
        if temporary.exists():
            os.unlink(temporary)
