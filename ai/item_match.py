from datetime import date
import math
import os

from ai.fuzzy_match import similarity
from ai.image_match import calculate_image_similarity


ITEM_TYPE_ALIASES = {
    "bag": "backpack",
    "rucksack": "backpack",
    "book bag": "backpack",
}

DESCRIPTION_EVIDENCE_MINIMUM = 30.0
BRAND_EVIDENCE_MINIMUM = 85.0
IMAGE_EVIDENCE_MINIMUM = 60.0
DEFAULT_MINIMUM_MATCH_SCORE = 45.0
DEFAULT_MATCH_WEIGHTS = {
    "item type": 0.25,
    "description": 0.30,
    "brand": 0.18,
    "color": 0.07,
    "location": 0.05,
    "date": 0.05,
    "photo": 0.10,
}


def normalize_text(value):
    """Normalize case, punctuation, and whitespace for report comparisons."""

    if not isinstance(value, str):
        return ""
    return " ".join(
        "".join(character if character.isalnum() else " " for character in value.casefold()).split()
    )


def canonical_item_type(value):
    """Return a canonical type using only explicitly defined aliases."""

    normalized = normalize_text(value)
    return ITEM_TYPE_ALIASES.get(normalized, normalized)


def _resolve_weights(weights):
    resolved = dict(DEFAULT_MATCH_WEIGHTS)
    if weights is None:
        return resolved
    if not isinstance(weights, dict):
        raise ValueError("Matching weights must be a mapping of criteria to numbers.")

    for criterion, value in weights.items():
        if criterion not in resolved:
            raise ValueError(f"Unknown matching criterion: {criterion}")
        try:
            weight = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError("Matching weights must be finite non-negative numbers.") from error
        if not math.isfinite(weight) or weight < 0:
            raise ValueError("Matching weights must be finite non-negative numbers.")
        resolved[criterion] = weight

    if not any(resolved.values()):
        raise ValueError("At least one matching weight must be greater than zero.")
    return resolved


def _report_key(report):
    identifier = report.get("id")
    if identifier is not None:
        return "id", str(identifier)
    return "record", repr(sorted(report.items(), key=lambda item: item[0]))


def hill_climb(initial_state, neighbors, score_fn):
    """Ascend to a local optimum by repeatedly taking the best improving neighbor."""

    current = initial_state
    current_score = float(score_fn(current))
    path = [current]
    evaluated = [current]

    while True:
        best_neighbor = None
        best_score = current_score
        for neighbor in neighbors(current):
            neighbor_score = float(score_fn(neighbor))
            evaluated.append(neighbor)
            if neighbor_score > best_score:
                best_neighbor = neighbor
                best_score = neighbor_score

        if best_neighbor is None:
            return {
                "state": current,
                "score": current_score,
                "path": path,
                "evaluated": evaluated,
            }

        current = best_neighbor
        current_score = best_score
        path.append(current)


def _date_score(left, right):
    try:
        difference = abs((date.fromisoformat(left) - date.fromisoformat(right)).days)
    except (TypeError, ValueError):
        return None

    if difference == 0:
        return 100.0
    if difference <= 2:
        return 75.0
    if difference <= 7:
        return 50.0
    if difference <= 30:
        return 25.0
    return 0.0


def _photo_score(lost, found):
    lost_path = lost.get("image_path")
    found_path = found.get("image_path")
    if (
        not isinstance(lost_path, str)
        or not isinstance(found_path, str)
        or not os.path.isfile(lost_path)
        or not os.path.isfile(found_path)
    ):
        return None

    try:
        with open(lost_path, "rb") as image_file:
            score = calculate_image_similarity(image_file.read(), found_path)
    except OSError:
        return None
    return float(score) if score is not None else None


def compare_items(lost, found, weights=None):
    """Explain whether two reports have enough evidence to be a candidate."""

    weights = _resolve_weights(weights)
    lost_type = canonical_item_type(lost.get("item_type"))
    found_type = canonical_item_type(found.get("item_type"))
    if not lost_type or not found_type:
        return {
            "credible": False,
            "score": 0.0,
            "reasons": ["Cannot compare reports because an item type is missing."],
            "criteria": {},
        }

    if lost_type != found_type:
        return {
            "credible": False,
            "score": 0.0,
            "reasons": [
                f"Incompatible item types: {lost.get('item_type')} vs {found.get('item_type')}."
            ],
            "criteria": {},
        }

    criteria = {"item type": 100.0}
    reasons = [
        f"Compatible item type: {lost.get('item_type')}"
        if normalize_text(lost.get("item_type")) == normalize_text(found.get("item_type"))
        else f"Compatible item types: {lost.get('item_type')} and {found.get('item_type')}"
    ]

    lost_description = normalize_text(lost.get("description"))
    found_description = normalize_text(found.get("description"))
    description_score = None
    if lost_description and found_description:
        description_score = round(
            similarity(lost_description, found_description) * 100,
            2,
        )
        criteria["description"] = description_score
        if description_score >= DESCRIPTION_EVIDENCE_MINIMUM:
            reasons.append(f"Descriptions have similar wording ({description_score:.0f}%).")
        else:
            reasons.append(f"Descriptions have little wording in common ({description_score:.0f}%).")

    lost_brand = normalize_text(lost.get("brand"))
    found_brand = normalize_text(found.get("brand"))
    brand_score = None
    if lost_brand and found_brand:
        brand_score = round(similarity(lost_brand, found_brand) * 100, 2)
        criteria["brand"] = brand_score
        brand_matches = brand_score >= BRAND_EVIDENCE_MINIMUM
        reasons.append(
            "Brand matches."
            if brand_matches else
            f"Brands differ ({brand_score:.0f}% text similarity)."
        )
    else:
        brand_matches = False

    lost_color = normalize_text(lost.get("color"))
    found_color = normalize_text(found.get("color"))
    if lost_color and found_color:
        color_matches = lost_color == found_color
        criteria["color"] = 100.0 if color_matches else 0.0
        reasons.append("Color matches." if color_matches else "Colors differ.")

    lost_location = normalize_text(lost.get("location"))
    found_location = normalize_text(found.get("location"))
    if lost_location and found_location:
        location_matches = lost_location == found_location
        criteria["location"] = 100.0 if location_matches else 0.0
        reasons.append(
            "Reported locations match."
            if location_matches
            else "Reported locations differ."
        )

    date_score = _date_score(lost.get("date"), found.get("date"))
    if date_score is not None:
        criteria["date"] = date_score
        if date_score == 100:
            reasons.append("Reports have the same date.")
        elif date_score > 0:
            reasons.append("Reports are within 30 days.")
        else:
            reasons.append("Report dates are more than 30 days apart.")

    image_score = _photo_score(lost, found)
    if image_score is not None:
        criteria["photo"] = float(image_score)
        if image_score >= IMAGE_EVIDENCE_MINIMUM:
            reasons.append(f"Photos are visually similar ({image_score:.0f}%).")
        else:
            reasons.append("Photos are not strongly similar.")

    has_identity_evidence = (
        (description_score is not None and description_score >= DESCRIPTION_EVIDENCE_MINIMUM)
        or brand_matches
        or (image_score is not None and image_score >= IMAGE_EVIDENCE_MINIMUM)
    )
    if not has_identity_evidence:
        reasons.append(
            "Rejected: matching type, color, date, or location alone is not enough; "
            "a matching description, brand, or photo is needed."
        )

    available_weight = sum(weights[name] for name in criteria)
    score = (
        round(
            sum(value * weights[name] for name, value in criteria.items())
            / available_weight,
            2,
        )
        if available_weight
        else 0.0
    )
    return {
        "credible": has_identity_evidence,
        "score": score,
        "reasons": reasons,
        "criteria": criteria,
    }


def find_item_matches(
    lost,
    found_items,
    weights=None,
    minimum_score=DEFAULT_MINIMUM_MATCH_SCORE,
    restarts=None,
):
    """Search compatible reports with multistart steepest-ascent Hill Climbing.

    Every compatible report is a neighbor of the current report. Starts are
    repeated from multiple candidates; scores are cached across restarts. The
    complete neighbor graph makes each restart inspect all candidates, so this
    search demonstrates Hill Climbing rather than reducing comparisons.
    """

    weights = _resolve_weights(weights)
    try:
        minimum_score = float(minimum_score)
    except (TypeError, ValueError) as error:
        raise ValueError("Minimum matching score must be between 0 and 100.") from error
    if not math.isfinite(minimum_score) or not 0 <= minimum_score <= 100:
        raise ValueError("Minimum matching score must be between 0 and 100.")

    unique_reports = []
    seen_reports = set()
    for found in found_items if isinstance(found_items, list) else []:
        if not isinstance(found, dict):
            continue
        if str(found.get("status", "Found")).strip().casefold() == "claimed":
            continue
        key = _report_key(found)
        if key in seen_reports:
            continue
        seen_reports.add(key)
        unique_reports.append(found)

    compatible = []
    rejected = []
    lost_type = canonical_item_type(lost.get("item_type"))
    for found in unique_reports:
        found_type = canonical_item_type(found.get("item_type"))
        if not lost_type or not found_type or lost_type != found_type:
            result = compare_items(lost, found, weights)
            rejected.append({"found": found, **result})
        else:
            compatible.append(found)

    if not compatible:
        return [], rejected

    try:
        restart_count = len(compatible) if restarts is None else int(restarts)
    except (TypeError, ValueError) as error:
        raise ValueError("Restart count must be a positive integer.") from error
    if restart_count <= 0:
        raise ValueError("Restart count must be a positive integer.")
    starting_candidates = compatible[:restart_count]

    comparison_cache = {}

    def score_candidate(candidate):
        key = _report_key(candidate)
        if key not in comparison_cache:
            comparison_cache[key] = compare_items(lost, candidate, weights)
        return comparison_cache[key]["score"]

    def candidate_neighbors(current):
        current_key = _report_key(current)
        return [
            candidate for candidate in compatible
            if _report_key(candidate) != current_key
        ]

    discovered = set()
    for initial_state in starting_candidates:
        search_result = hill_climb(
            initial_state,
            candidate_neighbors,
            score_candidate,
        )
        discovered.update(_report_key(state) for state in search_result["evaluated"])

    matches = []
    for found in compatible:
        key = _report_key(found)
        if key not in discovered:
            continue
        result = comparison_cache[key]
        if result["credible"] and result["score"] >= minimum_score:
            matches.append({"found": found, **result})
        else:
            reasons = list(result["reasons"])
            if result["credible"]:
                reasons.append(
                    f"Rejected: score {result['score']:.0f} is below the "
                    f"minimum of {minimum_score:.0f}."
                )
            rejected.append({"found": found, **result, "reasons": reasons})

    matches.sort(key=lambda match: match["score"], reverse=True)
    return matches, rejected