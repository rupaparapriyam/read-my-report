"""Read a lab report's text into results, and say which are outside range.

The one design decision that matters here: **the reference range is taken from the
report itself**, never from a table we wrote. Every Indian lab prints its own
biological reference interval beside each value, and those intervals genuinely differ
between labs, methods and machines. Reading the lab's own numbers means the comparison
is the lab's, not ours, and it keeps this file free of medical claims: deciding
"outside range" is then arithmetic, not an opinion about anyone's health.
"""
import re
from dataclasses import dataclass, asdict

# A number as a lab prints it: 9.8, 7,200, 2.6, 138
NUM = r"[0-9][0-9,]*(?:\.[0-9]+)?"
# Units a lab actually prints: g/dL, %, /cumm, lakh/cumm, uIU/mL, fL, mg/dL, 10^3/uL.
# Note the optional leading slash: Indian reports write counts as "/cumm".
UNIT = r"(?:%|/?[A-Za-zµμ][A-Za-z/µμ\^0-9\.\-]*)"

# "Haemoglobin   9.8   g/dL   12.0 - 15.0"  /  "Total Cholesterol  244  mg/dL  < 200"
ROW = re.compile(
    rf"^\s*(?P<test>[A-Za-z][A-Za-z0-9 ()\-/,\.'+]*?)\s{{2,}}"
    rf"(?P<value>{NUM})\s{{2,}}"
    rf"(?P<unit>{UNIT})?\s{{2,}}"
    rf"(?P<range>(?:{NUM}\s*[-–—to]+\s*{NUM})|(?:[<>≤≥]\s*{NUM}))\s*$")

SKIP = re.compile(r"\b(patient|age|sex|report no|collected|reported|referred|test\b.*result)",
                  re.I)


@dataclass
class Result:
    test: str
    value: float
    raw_value: str
    unit: str
    reference: str
    low: float = None
    high: float = None
    status: str = "unknown"       # low | normal | high | unknown
    distance: float = 0.0         # how far outside, as a share of the range width

    def as_dict(self):
        return asdict(self)


def _number(text):
    return float(text.replace(",", ""))


def _bounds(reference):
    """Turn '12.0 - 15.0', '< 200' or '> 40' into (low, high); None means open."""
    ref = reference.replace("–", "-").replace("—", "-").strip()
    pair = re.fullmatch(rf"({NUM})\s*(?:-|to)\s*({NUM})", ref, re.I)
    if pair:
        return _number(pair.group(1)), _number(pair.group(2))
    upper = re.fullmatch(rf"[<≤]\s*({NUM})", ref)
    if upper:
        return None, _number(upper.group(1))
    lower = re.fullmatch(rf"[>≥]\s*({NUM})", ref)
    if lower:
        return _number(lower.group(1)), None
    return None, None


def parse(text):
    """Text from a report (Textract, or pdftotext locally) -> list of Result."""
    results, seen = [], set()
    for line in text.splitlines():
        if SKIP.search(line):
            continue
        m = ROW.match(line.rstrip())
        if not m:
            continue
        test = " ".join(m.group("test").split())
        if test.lower() in seen:
            continue
        seen.add(test.lower())
        value = _number(m.group("value"))
        low, high = _bounds(m.group("range"))
        r = Result(test=test, value=value, raw_value=m.group("value"),
                   unit=(m.group("unit") or "").strip(), reference=m.group("range").strip(),
                   low=low, high=high)
        if low is None and high is None:
            r.status = "unknown"
        elif high is not None and value > high:
            r.status, r.distance = "high", _share(value - high, low, high)
        elif low is not None and value < low:
            r.status, r.distance = "low", _share(low - value, low, high)
        else:
            r.status = "normal"
        results.append(r)
    return results


def _share(gap, low, high):
    """How far outside, relative to the width of the normal band (0 if unknowable)."""
    if low is None or high is None:
        return round(gap / max(abs(low or high or 1), 1), 3)
    width = high - low
    return round(gap / width, 3) if width > 0 else 0.0


def summarise(results):
    out = [r for r in results if r.status in ("high", "low")]
    out.sort(key=lambda r: -r.distance)
    return {"total": len(results),
            "outside": len(out),
            "flagged": [r.test for r in out],
            "furthest": out[0].test if out else None}
