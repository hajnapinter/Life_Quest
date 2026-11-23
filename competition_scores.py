"""Whole-number competition totals without a per-quest ceiling or float rounding."""
import re


def score_text(value):
    """Return decimal digits for the numeric RPC, preserving large totals without float conversion."""
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]+', value.strip()):
        raise ValueError('A non-negative whole number is required.')
    return value.strip().lstrip('0') or '0'
