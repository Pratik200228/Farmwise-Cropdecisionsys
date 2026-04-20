from __future__ import annotations

import re
from dataclasses import dataclass
from time import time

from app.models import HealthIssue, HealthReport


@dataclass(frozen=True)
class HealthRule:
    keywords: re.Pattern[str]
    issue: dict[str, object]


HEALTH_RULES: tuple[HealthRule, ...] = (
    HealthRule(
        keywords=re.compile(r"yellow(ing)?|chloros", re.IGNORECASE),
        issue={
            "name": "Nitrogen deficiency",
            "kind": "nutrient",
            "severity": "watch",
            "symptoms": ["Uniform yellowing on older leaves", "Stunted new growth"],
            "treatment": ["Side-dress with urea or compost tea", "Split applications to avoid one heavy dose"],
            "preventive": ["Include legumes in rotation", "Test soil nitrogen every 2 seasons"],
        },
    ),
    HealthRule(
        keywords=re.compile(r"brown\s*spot|blight|lesion", re.IGNORECASE),
        issue={
            "name": "Early blight",
            "kind": "disease",
            "severity": "moderate",
            "symptoms": ["Concentric brown rings on lower leaves", "Yellow halo around lesions"],
            "treatment": ["Remove infected leaves", "Apply a labeled copper fungicide"],
            "preventive": ["Mulch to limit soil splash", "Rotate out of solanaceae for 2 seasons"],
        },
    ),
    HealthRule(
        keywords=re.compile(r"powder(y)?|white\s*film", re.IGNORECASE),
        issue={
            "name": "Powdery mildew",
            "kind": "disease",
            "severity": "moderate",
            "symptoms": ["White powdery film on leaf surfaces", "Leaf curling in late stages"],
            "treatment": ["Use sulfur or potassium bicarbonate spray", "Prune dense canopy for airflow"],
            "preventive": ["Water at the base instead of overhead", "Space plants for ventilation"],
        },
    ),
    HealthRule(
        keywords=re.compile(r"aphid|curl(ing)?\s*leaf|sticky", re.IGNORECASE),
        issue={
            "name": "Aphid infestation",
            "kind": "pest",
            "severity": "watch",
            "symptoms": ["Curling new leaves", "Sticky honeydew or sooty mold"],
            "treatment": ["Use a strong water jet on leaf undersides", "Apply neem oil at dusk"],
            "preventive": ["Encourage ladybugs and lacewings", "Avoid excess nitrogen that favors aphids"],
        },
    ),
    HealthRule(
        keywords=re.compile(r"wilt(ing)?|droop", re.IGNORECASE),
        issue={
            "name": "Water stress or vascular wilt",
            "kind": "water",
            "severity": "watch",
            "symptoms": ["Midday wilting", "No recovery overnight if vascular"],
            "treatment": ["Use deep, infrequent irrigation", "Dig a test plant and inspect roots and stem"],
            "preventive": ["Mulch to stabilize soil moisture", "Avoid overhead watering at midday"],
        },
    ),
    HealthRule(
        keywords=re.compile(r"hole|chew(ed)?|caterpillar|worm", re.IGNORECASE),
        issue={
            "name": "Caterpillar or leaf-feeding pest",
            "kind": "pest",
            "severity": "moderate",
            "symptoms": ["Irregular holes in leaves", "Frass on foliage"],
            "treatment": ["Hand-pick in the evening", "Apply Bt on young larvae"],
            "preventive": ["Use trap crops", "Scout weekly during warm, humid spells"],
        },
    ),
)


HEALTHY_ISSUE = HealthIssue(
    name="No significant issue detected",
    kind="disease",
    severity="healthy",
    probability=0.82,
    symptoms=["Canopy color is uniform", "No visible lesions or pests were reported"],
    treatment=["Continue weekly scouting"],
    preventive=["Maintain mulch and spacing", "Log photos weekly for trend tracking"],
)


def _severity_from_score(score: int) -> str:
    if score >= 85:
        return "healthy"
    if score >= 70:
        return "watch"
    if score >= 50:
        return "moderate"
    return "severe"


def build_health_report(crop: str, growth_stage: str, symptoms_note: str) -> HealthReport:
    note = symptoms_note.strip()
    issues: list[HealthIssue] = []
    seen: set[str] = set()

    for index, rule in enumerate(HEALTH_RULES):
        if rule.keywords.search(note):
            issue_name = str(rule.issue["name"])
            if issue_name in seen:
                continue
            seen.add(issue_name)
            probability = round(min(0.9, 0.62 + index * 0.04), 2)
            issues.append(HealthIssue(probability=probability, **rule.issue))

    health_score = 88 if not issues else max(40, 92 - len(issues) * 14)
    overall_severity = _severity_from_score(health_score)
    final_issues = issues or [HEALTHY_ISSUE]

    scouting_plan = [
        f"Walk {crop} rows every 3 days and photograph both leaf surfaces.",
        "Focus on border rows and low, humid spots where pressure starts first.",
        (
            "Flowering or fruiting is peak-risk; scout every 2 days."
            if growth_stage in {"flowering", "fruiting"}
            else "Log growth stage weekly so the model can tune expectations."
        ),
        (
            "If lesions spread to more than 15% of plants within 5 days, escalate to extension support."
            if any(issue.kind == "disease" for issue in final_issues)
            else "If an unknown pattern appears, send photos through the crop health API before spraying."
        ),
    ]

    return HealthReport(
        crop=crop,
        growthStage=growth_stage,
        healthScore=health_score,
        overallSeverity=overall_severity,
        issues=final_issues,
        scoutingPlan=scouting_plan,
        source="Fallback health ruleset (replace with PlantVillage or Plantix integrations)",
        generatedAt=round(time() * 1000),
    )
