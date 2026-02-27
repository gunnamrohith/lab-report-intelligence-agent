"""
ai_summary.py – Generate an intelligent health summary via OpenAI.

Responsibilities
-----------------
1. Build a concise prompt from the analysis report.
2. Call the OpenAI Chat Completions API.
3. Return a structured summary with:
   - Plain‑language health overview
   - Diet suggestions
   - Lifestyle recommendations
4. Gracefully fall back to a local rule‑based summary when the API key
   is missing or the call fails.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import List, Optional

from analyzer import AnalysisReport, AnalyzedTest, Status

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
# Data classes
# ──────────────────────────────────────────────────────────────────────


@dataclass
class HealthSummary:
    overview: str
    diet_suggestions: str
    lifestyle_recommendations: str
    generated_by: str  # "openai" or "rule-based"


# ──────────────────────────────────────────────────────────────────────
# Prompt builder
# ──────────────────────────────────────────────────────────────────────


def _build_prompt(report: AnalysisReport) -> str:
    """Compose a system + user prompt from the analysis report."""
    lines: list[str] = []
    for t in report.matched:
        flag = f"[{t.status.value}]" if t.status != Status.NORMAL else "[Normal]"
        lines.append(
            f"- {t.canonical_name.title()}: {t.value} {t.unit} "
            f"(ref: {t.min_value}–{t.max_value} {t.unit}) {flag}"
        )
    test_list = "\n".join(lines) if lines else "No recognized lab values."

    prompt = (
        "You are a board‑certified clinical laboratory scientist and "
        "nutrition advisor. Given the following lab report results, provide:\n\n"
        "1. **Health Overview** – A 2‑3 sentence summary of the patient's status.\n"
        "2. **Diet Suggestions** – Up to 3 key dietary changes (one line each).\n"
        "3. **Lifestyle Recommendations** – Up to 3 actionable tips (one line each).\n\n"
        "Be VERY concise — keep the entire response under 200 words. "
        "Use markdown formatting.\n\n"
        f"**Lab Results (Health Score: {report.health_score}/100):**\n{test_list}"
    )
    return prompt


# ──────────────────────────────────────────────────────────────────────
# OpenAI call
# ──────────────────────────────────────────────────────────────────────


def _call_openai(prompt: str, api_key: str, model: str = "gpt-4o-mini") -> Optional[str]:
    """Call OpenAI Chat Completions. Returns response text or None on error."""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful medical‑lab assistant. "
                        "Always add a note that this is informational only and "
                        "not a substitute for professional medical advice."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=800,
        )
        return response.choices[0].message.content
    except Exception as exc:
        logger.warning("OpenAI API call failed: %s", exc)
        return None


# ──────────────────────────────────────────────────────────────────────
# Rule‑based fallback
# ──────────────────────────────────────────────────────────────────────

_DIET_RULES: dict[str, dict[str, str]] = {
    "hemoglobin": {
        "Low": "Include iron‑rich foods: spinach, lentils, red meat, fortified cereals. Pair with vitamin C sources.",
        "High": "Stay well‑hydrated and moderate red‑meat intake. Consult a physician.",
    },
    "total cholesterol": {
        "High": "Reduce saturated fats (fried food, butter). Add oats, nuts, and fatty fish.",
    },
    "ldl": {
        "High": "Cut trans fats, increase soluble fiber (beans, oats), eat more omega‑3 fatty fish.",
    },
    "hdl": {
        "Low": "Add olive oil, avocado, nuts, and regular aerobic exercise to raise HDL levels.",
    },
    "triglycerides": {
        "High": "Limit sugar and refined carbs. Increase omega‑3 (salmon, walnuts). Avoid alcohol.",
    },
    "fasting glucose": {
        "High": "Reduce refined sugars and processed carbs. Eat whole grains, vegetables, lean protein.",
        "Low": "Eat small frequent meals with protein and complex carbs to stabilize blood sugar.",
    },
    "hba1c": {
        "High": "Follow a low‑glycaemic diet. Monitor carb portions. Increase fiber intake.",
    },
    "creatinine": {
        "High": "Stay hydrated. Moderate protein intake. Limit sodium and processed foods.",
    },
    "uric acid": {
        "High": "Avoid organ meats, shellfish, alcohol — especially beer. Drink plenty of water.",
    },
    "tsh": {
        "High": "Ensure adequate iodine and selenium. Limit goitrogenic raw cruciferous vegetables.",
        "Low": "Avoid excess iodine supplements. Include anti‑inflammatory foods.",
    },
    "vitamin d": {
        "Low": "Get 15–20 min of sunlight daily. Eat fortified dairy, eggs, fatty fish. Consider supplementation.",
    },
    "vitamin b12": {
        "Low": "Eat eggs, dairy, fortified cereals, or consider B12 supplements (especially if vegan).",
    },
    "iron": {
        "Low": "Add iron‑rich foods (red meat, spinach, lentils) and vitamin C to enhance absorption.",
        "High": "Limit red meat and iron supplements. Avoid alcohol. Consult a physician.",
    },
    "ferritin": {
        "Low": "Increase dietary iron with lean meats, beans, and dark leafy greens.",
        "High": "Reduce iron‑rich food intake and avoid vitamin C supplements with meals.",
    },
    "sgpt": {
        "High": "Avoid alcohol and processed foods. Eat cruciferous vegetables, garlic, and turmeric.",
    },
    "sgot": {
        "High": "Minimize alcohol, eat a balanced diet, include antioxidant‑rich foods.",
    },
    "calcium": {
        "Low": "Add dairy, fortified plant milks, and leafy greens. Consider vitamin D co‑supplementation.",
        "High": "Reduce dairy intake and consult a physician. Stay hydrated.",
    },
    "potassium": {
        "Low": "Eat bananas, oranges, potatoes, and spinach.",
        "High": "Limit bananas, potatoes, and tomatoes. Avoid salt substitutes with KCl.",
    },
    "sodium": {
        "High": "Reduce salt, processed, and canned foods. Drink more water.",
        "Low": "Add moderate salt. Avoid excessive water intake. Consult a physician.",
    },
}

_LIFESTYLE_RULES: dict[str, dict[str, str]] = {
    "hemoglobin": {
        "Low": "Moderate exercise; avoid intense workouts until levels improve. Prioritize sleep.",
    },
    "total cholesterol": {
        "High": "30 min brisk walking daily. Manage stress. Quit smoking if applicable.",
    },
    "ldl": {
        "High": "Regular aerobic exercise (5×/week, 30 min). Maintain healthy weight.",
    },
    "hdl": {
        "Low": "Regular cardio exercise, quit smoking, maintain a healthy BMI.",
    },
    "triglycerides": {
        "High": "Regular exercise. Limit alcohol. Maintain healthy weight.",
    },
    "fasting glucose": {
        "High": "Daily 30‑min walks. Manage stress. Get 7‑8 h of sleep.",
        "Low": "Avoid skipping meals. Keep healthy snacks handy.",
    },
    "hba1c": {
        "High": "Consistent daily exercise. Monitor blood sugar. Reduce stress.",
    },
    "creatinine": {
        "High": "Avoid heavy‑resistance training temporarily. Stay well‑hydrated. Reduce NSAID use.",
    },
    "uric acid": {
        "High": "Stay hydrated. Maintain healthy weight. Avoid crash diets.",
    },
    "tsh": {
        "High": "Regular exercise. Manage stress with yoga or meditation. Ensure adequate sleep.",
        "Low": "Gentle, low‑impact exercise. Prioritize rest. Avoid caffeine excess.",
    },
    "vitamin d": {
        "Low": "Spend 15–20 min outdoors in sunlight. Engage in outdoor activities.",
    },
    "esr": {
        "High": "Practice stress management. Sleep 7‑8 h. Consider anti‑inflammatory lifestyle changes.",
    },
    "crp": {
        "High": "Regular moderate exercise. Manage stress. Aim for healthy BMI.",
    },
    "sgpt": {
        "High": "Avoid alcohol. Exercise regularly. Maintain a healthy weight.",
    },
    "sgot": {
        "High": "Limit alcohol. Rest adequately. Manage weight.",
    },
}


def _rule_based_summary(report: AnalysisReport) -> HealthSummary:
    """Generate a deterministic summary without an LLM."""
    abnormal = [t for t in report.matched if t.status != Status.NORMAL]

    # ── Overview ──
    if not abnormal:
        overview = (
            "All recognized lab values are within normal limits. "
            "Your overall health indicators look good! Continue maintaining "
            "a balanced diet and active lifestyle."
        )
    else:
        items = ", ".join(
            f"**{t.canonical_name.title()}** ({t.status.value})" for t in abnormal
        )
        overview = (
            f"Out of {len(report.matched)} recognized tests, "
            f"{len(abnormal)} require attention: {items}. "
            f"Your health score is **{report.health_score}/100**."
        )

    # ── Diet ──
    diet_parts: list[str] = []
    for t in abnormal:
        key = t.canonical_name
        direction = t.status.value
        suggestion = _DIET_RULES.get(key, {}).get(direction)
        if suggestion:
            diet_parts.append(f"- **{key.title()}** ({direction}): {suggestion}")
    diet = "\n".join(diet_parts) if diet_parts else "- Maintain a balanced, nutrient‑rich diet."

    # ── Lifestyle ──
    lifestyle_parts: list[str] = []
    for t in abnormal:
        key = t.canonical_name
        direction = t.status.value
        suggestion = _LIFESTYLE_RULES.get(key, {}).get(direction)
        if suggestion:
            lifestyle_parts.append(f"- **{key.title()}** ({direction}): {suggestion}")
    lifestyle = (
        "\n".join(lifestyle_parts)
        if lifestyle_parts
        else "- Stay active with 30 min of moderate exercise daily.\n- Sleep 7–8 hours per night."
    )

    return HealthSummary(
        overview=overview,
        diet_suggestions=diet,
        lifestyle_recommendations=lifestyle,
        generated_by="rule-based",
    )


# ──────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────


def generate_summary(
    report: AnalysisReport,
    api_key: Optional[str] = None,
    model: str = "gpt-4o-mini",
) -> HealthSummary:
    """
    Generate a health summary from the analysis report.

    Uses OpenAI when *api_key* is provided and the API call succeeds;
    otherwise falls back to a rule‑based summary.
    """
    if api_key:
        prompt = _build_prompt(report)
        raw = _call_openai(prompt, api_key, model=model)
        if raw:
            # Split the AI response into sections heuristically
            sections = _split_ai_response(raw)
            return HealthSummary(
                overview=sections.get("overview", raw),
                diet_suggestions=sections.get("diet", "See overview for details."),
                lifestyle_recommendations=sections.get(
                    "lifestyle", "See overview for details."
                ),
                generated_by="openai",
            )
        logger.info("OpenAI unavailable — falling back to rule‑based summary.")

    return _rule_based_summary(report)


def _split_ai_response(text: str) -> dict[str, str]:
    """Best‑effort split of the AI markdown response into named sections."""
    import re

    sections: dict[str, str] = {}
    # Try to split on markdown headings
    parts = re.split(r"\n(?=#{1,3}\s)", text)
    for part in parts:
        lower = part.lower()
        if "overview" in lower or "summary" in lower or "health" in lower[:60]:
            sections.setdefault("overview", part.strip())
        elif "diet" in lower or "nutrition" in lower or "food" in lower:
            sections.setdefault("diet", part.strip())
        elif "lifestyle" in lower or "exercise" in lower or "recommendation" in lower:
            sections.setdefault("lifestyle", part.strip())

    # If splitting failed, put everything in overview
    if not sections:
        sections["overview"] = text.strip()

    return sections


# ──────────────────────────────────────────────────────────────────────
# Health Interpretation & Food Guidance
# ──────────────────────────────────────────────────────────────────────

_HEALTH_GUIDANCE_SYSTEM_PROMPT = (
    "You are a medical assistant explaining lab results in very simple language "
    "for a patient. Do not diagnose. Provide educational dietary and lifestyle "
    "advice only. Always recommend consulting a doctor."
)


def _build_health_guidance_prompt(abnormal_tests: List[AnalyzedTest], health_score: int) -> str:
    """Build a detailed prompt for health interpretation and food guidance."""
    lines: list[str] = []
    for t in abnormal_tests:
        lines.append(
            f"- {t.canonical_name.title()}: {t.value} {t.unit} "
            f"(Reference: {t.min_value}–{t.max_value} {t.unit}) — Status: {t.status.value}"
        )
    test_block = "\n".join(lines)

    return (
        f"A patient has a health score of {health_score}/100.\n"
        f"The following lab values are ABNORMAL:\n\n{test_block}\n\n"
        "Provide BRIEF sections in clean markdown (keep ENTIRE response under 250 words):\n\n"
        "## 🩺 Simple Explanation\n"
        "- One short sentence per abnormal value in plain language.\n\n"
        "## 🥗 What Foods to Eat\n"
        "- 2‑3 top foods to eat and 1‑2 to avoid per condition (one line each).\n\n"
        "## 🏃 Lifestyle Changes\n"
        "- 2‑3 practical, one-line tips total.\n\n"
        "## ⚕️ When to Consult a Doctor\n"
        "- 1‑2 sentences only.\n\n"
        "Be concise and calm."
    )


def _call_health_guidance_openai(
    prompt: str, api_key: str, model: str = "gpt-4o-mini"
) -> Optional[str]:
    """Call OpenAI with the health-guidance system prompt."""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _HEALTH_GUIDANCE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=800,
        )
        return response.choices[0].message.content
    except Exception as exc:
        logger.warning("OpenAI health-guidance call failed: %s", exc)
        return None


def _rule_based_health_guidance(abnormal_tests: List[AnalyzedTest], health_score: int) -> str:
    """Generate a local rule-based health guidance markdown when no API key."""
    parts: list[str] = []

    # Section 1: Simple Explanation
    parts.append("## 🩺 Simple Explanation\n")
    if not abnormal_tests:
        parts.append("All your lab values are within the normal range — great news!\n")
    else:
        for t in abnormal_tests:
            direction = "low" if t.status == Status.LOW else "high"
            parts.append(
                f"- **{t.canonical_name.title()}** is {direction} "
                f"({t.value} vs {t.min_value}–{t.max_value} {t.unit}).\n"
            )

    # Section 2: What Foods to Eat
    parts.append("\n## 🥗 What Foods to Eat\n")
    any_diet = False
    for t in abnormal_tests:
        key = t.canonical_name
        direction = t.status.value
        suggestion = _DIET_RULES.get(key, {}).get(direction)
        if suggestion:
            any_diet = True
            parts.append(f"- **{key.title()}:** {suggestion}\n")
    if not any_diet:
        parts.append("- Balanced diet: fruits, vegetables, whole grains, lean protein.\n")

    # Section 3: Lifestyle Changes
    parts.append("\n## 🏃 Lifestyle Changes\n")
    any_lifestyle = False
    for t in abnormal_tests:
        key = t.canonical_name
        direction = t.status.value
        suggestion = _LIFESTYLE_RULES.get(key, {}).get(direction)
        if suggestion:
            any_lifestyle = True
            parts.append(f"- **{key.title()}:** {suggestion}\n")
    if not any_lifestyle:
        parts.append(
            "- 30 min moderate exercise daily, 7‑8 h sleep, stay hydrated.\n"
        )

    # Section 4: When to Consult a Doctor
    parts.append("\n## ⚕️ When to Consult a Doctor\n")
    parts.append(
        "- Consult your doctor if values are far outside normal range or you have symptoms. "
        "*This report is educational only — not a diagnosis.*\n"
    )

    return "\n".join(parts)


def generate_health_guidance(
    report: AnalysisReport,
    api_key: Optional[str] = None,
    model: str = "gpt-4o-mini",
) -> str:
    """
    Generate AI Health Interpretation & Food Guidance markdown.

    Uses OpenAI when *api_key* is provided; otherwise falls back to
    a rule-based local summary. Only considers abnormal values.

    Returns
    -------
    str
        Markdown-formatted health guidance text.
    """
    abnormal = [t for t in report.matched if t.status != Status.NORMAL]

    if not abnormal:
        return (
            "## 🩺 All Clear!\n\n"
            "All your lab values are within normal limits. "
            "Keep up the great work with your current diet and lifestyle!\n\n"
            "_Remember: regular check-ups are important. Consult your doctor "
            "for routine health screenings._"
        )

    if api_key:
        prompt = _build_health_guidance_prompt(abnormal, report.health_score)
        raw = _call_health_guidance_openai(prompt, api_key, model=model)
        if raw:
            return raw
        logger.info("OpenAI health-guidance unavailable — falling back to rule-based.")

    return _rule_based_health_guidance(abnormal, report.health_score)
