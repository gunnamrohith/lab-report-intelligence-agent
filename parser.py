"""
parser.py – PDF text extraction and lab‑value parsing.

Responsibilities
-----------------
1. Extract raw text from an uploaded PDF via *pdfplumber*.
2. Parse (test_name, numeric_value) pairs using regex heuristics.
3. Return structured results ready for the analyzer module.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from io import BytesIO
from typing import BinaryIO, List, Optional, Sequence

import pdfplumber

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
# Data classes
# ──────────────────────────────────────────────────────────────────────


@dataclass
class ExtractedTest:
    """A single lab test name + numeric value extracted from text."""

    raw_name: str  # original text as found on the report
    value: float
    line: str  # source line for traceability


class PDFExtractionError(Exception):
    """Raised when text cannot be extracted from the PDF."""


class EmptyPDFError(PDFExtractionError):
    """Raised when the PDF yields no extractable text."""


# ──────────────────────────────────────────────────────────────────────
# PDF → text
# ──────────────────────────────────────────────────────────────────────


def extract_text_from_pdf(file: BinaryIO | BytesIO) -> str:
    """
    Read every page of *file* and return concatenated text.

    Raises
    ------
    EmptyPDFError
        When no text can be extracted (scanned image, encrypted, etc.).
    PDFExtractionError
        For any other PDF‑related issue.
    """
    try:
        with pdfplumber.open(file) as pdf:
            if not pdf.pages:
                raise EmptyPDFError(
                    "The uploaded PDF has no pages. Please upload a valid lab report."
                )

            pages_text: list[str] = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)

            full_text = "\n".join(pages_text).strip()
            if not full_text:
                raise EmptyPDFError(
                    "Could not extract any text from the PDF. "
                    "The file may be a scanned image — please upload a text‑based PDF."
                )
            return full_text

    except EmptyPDFError:
        raise
    except Exception as exc:
        raise PDFExtractionError(f"Failed to read PDF: {exc}") from exc


# ──────────────────────────────────────────────────────────────────────
# Text → structured lab values
# ──────────────────────────────────────────────────────────────────────

# Lines / tokens to ignore — dates, metadata, headers, page numbers, etc.
_NOISE_PATTERNS = re.compile(
    r"""
    (?:^page\s)                     |   # "Page 1/2"
    (?:^date\s)                     |   # "Date of …"
    (?:^sample\s*id)                |   # "Sample ID"
    (?:^patient\s)                  |   # "Patient Name"
    (?:^referred\s)                 |   # "Referred By"
    (?:^age\s)                      |   # "Age / Gender"
    (?:^test\s+name\b)              |   # column header row
    (?:^this\s+report)              |   # footer disclaimer
    (?:\*{2,})                      |   # "*** End of Report ***"
    (?:^dr\.\s)                     |   # doctor signature
    (?:^chief\s)                        # "Chief Laboratory Director"
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _is_noise(line: str) -> bool:
    """Return True if the line is clearly not a lab-test row."""
    stripped = line.strip()
    if len(stripped) < 4:
        return True
    return bool(_NOISE_PATTERNS.search(stripped))


# ── Primary pattern : <Name>  <Result>  <Unit>  <Ref range…> ──
# Captures the FIRST numeric token after an alphabetic test name.
# The name must start with a letter and may contain letters, digits,
# spaces, hyphens, slashes, parens, commas, colons, and periods that
# are NOT part of a decimal number.
_TABULAR_PATTERN = re.compile(
    r"""
    ^
    \s*
    (?P<name>[A-Za-z][A-Za-z0-9 /\-\(\),.:']*?)  # test name (lazy)
    \s*[:\.\-–—]*\s+                               # separator / whitespace
    (?P<value>\d+(?:\.\d+)?)                        # FIRST numeric value = result
    \b
    """,
    re.VERBOSE,
)

# ── Colon-separated: "Test Name : 13.5 g/dL" ──
_COLON_PATTERN = re.compile(
    r"""
    ^
    \s*
    (?P<name>[A-Za-z][A-Za-z0-9 /\-\(\),.:']+?)
    \s*:\s*
    (?P<value>\d+(?:\.\d+)?)
    \b
    """,
    re.VERBOSE,
)


def _clean_name(raw: str) -> str:
    """Normalise whitespace and strip trailing punctuation from a test name."""
    name = re.sub(r"\s+", " ", raw).strip()
    name = name.rstrip(":.- ")
    return name


def parse_lab_values(text: str) -> List[ExtractedTest]:
    """
    Parse lab test names and numeric values from *text*.

    Strategy
    --------
    1. Split text into lines.
    2. Skip noise lines (dates, headers, footers, etc.).
    3. For each remaining line, try to extract (name, first_number).
    4. Deduplicate on cleaned name.

    Returns
    -------
    list[ExtractedTest]
        Parsed results (may be empty if nothing matched).
    """
    seen: dict[str, ExtractedTest] = {}

    def _add(name: str, value_str: str, line: str) -> None:
        cleaned = _clean_name(name)
        if not cleaned or len(cleaned) < 2:
            return
        # Skip names that are purely numeric or very short single chars
        if re.fullmatch(r"[\d\s.]+", cleaned):
            return
        try:
            val = float(value_str)
        except ValueError:
            return
        key = cleaned.lower()
        if key not in seen:
            seen[key] = ExtractedTest(raw_name=cleaned, value=val, line=line.strip())

    for line in text.splitlines():
        if _is_noise(line):
            continue

        # Try colon-separated first (higher confidence)
        m = _COLON_PATTERN.match(line)
        if m:
            _add(m.group("name"), m.group("value"), line)
            continue

        # Then tabular layout (most common in lab PDFs)
        m = _TABULAR_PATTERN.match(line)
        if m:
            _add(m.group("name"), m.group("value"), line)

    results = list(seen.values())
    logger.info("Parsed %d lab value(s) from text.", len(results))
    return results
