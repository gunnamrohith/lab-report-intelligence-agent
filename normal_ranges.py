"""
Normal reference ranges for common lab tests.

Each entry maps a canonical test name to:
  - min / max : inclusive boundaries for the "Normal" classification
  - unit      : display unit
  - aliases   : alternate spellings / abbreviations found on reports

Values are based on widely‑accepted adult reference intervals.
Sources: Mayo Clinic, MedlinePlus, WHO guidelines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ReferenceRange:
    """Immutable reference range for a single lab test."""

    min_value: float
    max_value: float
    unit: str
    aliases: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Master dictionary – keys are *canonical* (lower‑case) test names.
# ---------------------------------------------------------------------------

NORMAL_RANGES: Dict[str, ReferenceRange] = {
    # Complete Blood Count (CBC)
    "hemoglobin": ReferenceRange(
        min_value=12.0,
        max_value=17.5,
        unit="g/dL",
        aliases=("hb", "hgb", "haemoglobin"),
    ),
    "hematocrit": ReferenceRange(
        min_value=36.0,
        max_value=50.0,
        unit="%",
        aliases=("hct", "pcv", "packed cell volume"),
    ),
    "rbc": ReferenceRange(
        min_value=4.0,
        max_value=6.0,
        unit="million/µL",
        aliases=("red blood cells", "red blood cell count", "rbc count", "erythrocytes"),
    ),
    "wbc": ReferenceRange(
        min_value=4.0,
        max_value=11.0,
        unit="thousand/µL",
        aliases=(
            "white blood cells",
            "white blood cell count",
            "wbc count",
            "leukocytes",
            "total wbc",
            "total leucocyte count",
            "tlc",
        ),
    ),
    "platelets": ReferenceRange(
        min_value=150.0,
        max_value=400.0,
        unit="thousand/µL",
        aliases=("platelet count", "plt", "thrombocytes"),
    ),
    "mcv": ReferenceRange(
        min_value=80.0,
        max_value=100.0,
        unit="fL",
        aliases=("mean corpuscular volume",),
    ),
    "mch": ReferenceRange(
        min_value=27.0,
        max_value=33.0,
        unit="pg",
        aliases=("mean corpuscular hemoglobin",),
    ),
    "mchc": ReferenceRange(
        min_value=32.0,
        max_value=36.0,
        unit="g/dL",
        aliases=("mean corpuscular hemoglobin concentration",),
    ),
    "rdw": ReferenceRange(
        min_value=11.5,
        max_value=14.5,
        unit="%",
        aliases=("red cell distribution width", "rdw-cv"),
    ),
    "mpv": ReferenceRange(
        min_value=7.5,
        max_value=11.5,
        unit="fL",
        aliases=("mean platelet volume",),
    ),

    # Lipid Panel
    "total cholesterol": ReferenceRange(
        min_value=0.0,
        max_value=200.0,
        unit="mg/dL",
        aliases=("cholesterol", "cholesterol total", "tc", "serum cholesterol"),
    ),
    "ldl": ReferenceRange(
        min_value=0.0,
        max_value=100.0,
        unit="mg/dL",
        aliases=(
            "ldl cholesterol",
            "ldl-c",
            "low density lipoprotein",
            "bad cholesterol",
        ),
    ),
    "hdl": ReferenceRange(
        min_value=40.0,
        max_value=60.0,
        unit="mg/dL",
        aliases=(
            "hdl cholesterol",
            "hdl-c",
            "high density lipoprotein",
            "good cholesterol",
        ),
    ),
    "triglycerides": ReferenceRange(
        min_value=0.0,
        max_value=150.0,
        unit="mg/dL",
        aliases=("tg", "trigs", "triglyceride"),
    ),
    "vldl": ReferenceRange(
        min_value=2.0,
        max_value=30.0,
        unit="mg/dL",
        aliases=("vldl cholesterol", "very low density lipoprotein"),
    ),

    # Liver Function Tests (LFT)
    "sgot": ReferenceRange(
        min_value=5.0,
        max_value=40.0,
        unit="U/L",
        aliases=("ast", "aspartate aminotransferase", "sgot (ast)"),
    ),
    "sgpt": ReferenceRange(
        min_value=7.0,
        max_value=56.0,
        unit="U/L",
        aliases=("alt", "alanine aminotransferase", "sgpt (alt)"),
    ),
    "alkaline phosphatase": ReferenceRange(
        min_value=44.0,
        max_value=147.0,
        unit="U/L",
        aliases=("alp", "alk phos", "alkp"),
    ),
    "total bilirubin": ReferenceRange(
        min_value=0.1,
        max_value=1.2,
        unit="mg/dL",
        aliases=("bilirubin", "bilirubin total", "t. bilirubin", "tbil"),
    ),
    "direct bilirubin": ReferenceRange(
        min_value=0.0,
        max_value=0.3,
        unit="mg/dL",
        aliases=("conjugated bilirubin", "d. bilirubin", "dbil"),
    ),
    "albumin": ReferenceRange(
        min_value=3.5,
        max_value=5.5,
        unit="g/dL",
        aliases=("serum albumin", "alb"),
    ),
    "globulin": ReferenceRange(
        min_value=2.0,
        max_value=3.5,
        unit="g/dL",
        aliases=("serum globulin",),
    ),
    "total protein": ReferenceRange(
        min_value=6.0,
        max_value=8.3,
        unit="g/dL",
        aliases=("protein total", "tp", "serum protein"),
    ),
    "ag ratio": ReferenceRange(
        min_value=1.0,
        max_value=2.5,
        unit="",
        aliases=("albumin/globulin ratio", "a/g ratio", "a:g ratio"),
    ),
    "ggt": ReferenceRange(
        min_value=0.0,
        max_value=45.0,
        unit="U/L",
        aliases=("gamma gt", "gamma-glutamyl transferase", "ggtp"),
    ),

    # Kidney / Renal Function
    "creatinine": ReferenceRange(
        min_value=0.6,
        max_value=1.2,
        unit="mg/dL",
        aliases=("serum creatinine", "creat", "s. creatinine"),
    ),
    "bun": ReferenceRange(
        min_value=7.0,
        max_value=20.0,
        unit="mg/dL",
        aliases=("blood urea nitrogen", "urea nitrogen"),
    ),
    "urea": ReferenceRange(
        min_value=15.0,
        max_value=45.0,
        unit="mg/dL",
        aliases=("blood urea", "serum urea"),
    ),
    "uric acid": ReferenceRange(
        min_value=3.0,
        max_value=7.0,
        unit="mg/dL",
        aliases=("serum uric acid", "urate"),
    ),
    "egfr": ReferenceRange(
        min_value=90.0,
        max_value=120.0,
        unit="mL/min/1.73m²",
        aliases=(
            "estimated gfr",
            "glomerular filtration rate",
            "estimated glomerular filtration rate",
        ),
    ),

    # Diabetes / Metabolic
    "fasting glucose": ReferenceRange(
        min_value=70.0,
        max_value=100.0,
        unit="mg/dL",
        aliases=(
            "fasting blood sugar",
            "fbs",
            "glucose fasting",
            "fasting plasma glucose",
            "fpg",
            "blood sugar fasting",
        ),
    ),
    "random glucose": ReferenceRange(
        min_value=70.0,
        max_value=140.0,
        unit="mg/dL",
        aliases=("random blood sugar", "rbs", "glucose random", "blood sugar random"),
    ),
    "hba1c": ReferenceRange(
        min_value=4.0,
        max_value=5.6,
        unit="%",
        aliases=(
            "glycated hemoglobin",
            "glycosylated hemoglobin",
            "a1c",
            "hemoglobin a1c",
            "hb a1c",
        ),
    ),
    "pp glucose": ReferenceRange(
        min_value=70.0,
        max_value=140.0,
        unit="mg/dL",
        aliases=(
            "postprandial glucose",
            "post prandial blood sugar",
            "ppbs",
            "glucose pp",
        ),
    ),

    # Thyroid Panel
    "tsh": ReferenceRange(
        min_value=0.4,
        max_value=4.0,
        unit="mIU/L",
        aliases=("thyroid stimulating hormone", "thyrotropin"),
    ),
    "t3": ReferenceRange(
        min_value=80.0,
        max_value=200.0,
        unit="ng/dL",
        aliases=("triiodothyronine", "total t3", "serum t3"),
    ),
    "t4": ReferenceRange(
        min_value=5.0,
        max_value=12.0,
        unit="µg/dL",
        aliases=("thyroxine", "total t4", "serum t4"),
    ),
    "free t3": ReferenceRange(
        min_value=2.3,
        max_value=4.2,
        unit="pg/mL",
        aliases=("ft3",),
    ),
    "free t4": ReferenceRange(
        min_value=0.8,
        max_value=1.8,
        unit="ng/dL",
        aliases=("ft4", "free thyroxine"),
    ),

    # Electrolytes
    "sodium": ReferenceRange(
        min_value=136.0,
        max_value=145.0,
        unit="mEq/L",
        aliases=("na", "na+", "serum sodium"),
    ),
    "potassium": ReferenceRange(
        min_value=3.5,
        max_value=5.0,
        unit="mEq/L",
        aliases=("k", "k+", "serum potassium"),
    ),
    "chloride": ReferenceRange(
        min_value=98.0,
        max_value=106.0,
        unit="mEq/L",
        aliases=("cl", "cl-", "serum chloride"),
    ),
    "calcium": ReferenceRange(
        min_value=8.5,
        max_value=10.5,
        unit="mg/dL",
        aliases=("ca", "serum calcium", "total calcium"),
    ),
    "phosphorus": ReferenceRange(
        min_value=2.5,
        max_value=4.5,
        unit="mg/dL",
        aliases=("phosphate", "serum phosphorus", "po4"),
    ),
    "magnesium": ReferenceRange(
        min_value=1.7,
        max_value=2.2,
        unit="mg/dL",
        aliases=("mg", "serum magnesium"),
    ),

    # Iron Studies
    "iron": ReferenceRange(
        min_value=60.0,
        max_value=170.0,
        unit="µg/dL",
        aliases=("serum iron", "fe"),
    ),
    "ferritin": ReferenceRange(
        min_value=12.0,
        max_value=300.0,
        unit="ng/mL",
        aliases=("serum ferritin",),
    ),
    "tibc": ReferenceRange(
        min_value=250.0,
        max_value=370.0,
        unit="µg/dL",
        aliases=("total iron binding capacity",),
    ),

    # Vitamins
    "vitamin d": ReferenceRange(
        min_value=30.0,
        max_value=100.0,
        unit="ng/mL",
        aliases=("25-hydroxy vitamin d", "25(oh)d", "vit d", "vitamin d3"),
    ),
    "vitamin b12": ReferenceRange(
        min_value=200.0,
        max_value=900.0,
        unit="pg/mL",
        aliases=("b12", "cobalamin", "vit b12"),
    ),
    "folate": ReferenceRange(
        min_value=2.7,
        max_value=17.0,
        unit="ng/mL",
        aliases=("folic acid", "serum folate", "vitamin b9"),
    ),

    # Inflammation / Cardiac
    "esr": ReferenceRange(
        min_value=0.0,
        max_value=20.0,
        unit="mm/hr",
        aliases=("erythrocyte sedimentation rate", "sed rate"),
    ),
    "crp": ReferenceRange(
        min_value=0.0,
        max_value=3.0,
        unit="mg/L",
        aliases=("c-reactive protein", "c reactive protein", "hs-crp"),
    ),

    # Prostate
    "psa": ReferenceRange(
        min_value=0.0,
        max_value=4.0,
        unit="ng/mL",
        aliases=("prostate specific antigen",),
    ),
}


# ---------------------------------------------------------------------------
# Helper look‑up function
# ---------------------------------------------------------------------------


def _build_alias_map() -> Dict[str, str]:
    """Build a reverse‑lookup dict: alias → canonical name."""
    alias_map: Dict[str, str] = {}
    for canonical, ref in NORMAL_RANGES.items():
        alias_map[canonical] = canonical
        for alias in ref.aliases:
            alias_map[alias.lower()] = canonical
    return alias_map


_ALIAS_MAP: Dict[str, str] = _build_alias_map()


def lookup(test_name: str) -> Optional[tuple[str, ReferenceRange]]:
    """
    Look up a test by name or alias (case‑insensitive).

    Returns
    -------
    (canonical_name, ReferenceRange) if found, else None.
    """
    key = test_name.strip().lower()
    canonical = _ALIAS_MAP.get(key)
    if canonical is None:
        return None
    return canonical, NORMAL_RANGES[canonical]
