import math
import os

from ai.fuzzy_match import calculate_match_details, calculate_match_score
from ai.image_match import calculate_image_similarity
from ai.semantic_match import (
    calculate_semantic_similarity,
    get_semantic_model_error,
)


DEFAULT_WEIGHTS = {
    "fuzzy": 30,
    "semantic": 40,
    "image": 20,
    "location": 10,
}


def _valid_score(value):
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(score):
        return None
    return max(0.0, min(100.0, score))


def _usable_text(value):
    return isinstance(value, str) and bool(value.strip())


def _fuzzy_detail_score(details, lost, found):
    """Aggregate existing fuzzy type/color/brand scores without overlap."""

    attribute_weights = {
        "item_type": 25,
        "color": 15,
        "brand": 15,
    }
    available = [
        (
            weight,
            _valid_score(details.get(field))
            if _usable_text(lost.get(field)) and _usable_text(found.get(field))
            else None,
        )
        for field, weight in attribute_weights.items()
    ]
    available = [
        (weight, score)
        for weight, score in available
        if score is not None
    ]
    if not available:
        return None
    return sum(weight * score for weight, score in available) / sum(
        weight for weight, _ in available
    )


def _image_score(lost, found):
    lost_path = lost.get("image_path")
    found_path = found.get("image_path")
    if not isinstance(lost_path, str) or not isinstance(found_path, str):
        return None
    if not lost_path or not found_path or not os.path.isfile(lost_path):
        return None
    if not os.path.isfile(found_path):
        return None

    try:
        with open(lost_path, "rb") as image_file:
            return _valid_score(
                calculate_image_similarity(image_file.read(), found_path)
            )
    except OSError:
        return None


def calculate_hybrid_match(
    lost,
    found,
    weights=None,
    semantic_scorer=None,
    image_scorer=None,
):
    """Return a normalized hybrid ranking score and available components."""

    if not isinstance(lost, dict) or not isinstance(found, dict):
        return {
            "score": 0.0,
            "components": {},
            "reasons": [],
            "fallback": False,
        }

    configured_weights = dict(DEFAULT_WEIGHTS)
    if isinstance(weights, dict):
        for component in configured_weights:
            candidate = _valid_score(weights.get(component))
            if candidate is not None:
                configured_weights[component] = candidate

    text_details = calculate_match_details(lost, found)
    fuzzy_score = _fuzzy_detail_score(text_details, lost, found)
    using_default_semantic_scorer = semantic_scorer is None
    semantic_scorer = semantic_scorer or calculate_semantic_similarity
    image_scorer = image_scorer or _image_score

    lost_description = lost.get("description")
    found_description = found.get("description")
    semantic_score = None
    if _usable_text(lost_description) and _usable_text(found_description):
        try:
            semantic_score = _valid_score(
                semantic_scorer(lost_description, found_description)
            )
        except Exception:
            semantic_score = None

    image_score = None
    try:
        image_score = _valid_score(image_scorer(lost, found))
    except Exception:
        image_score = None

    lost_location = lost.get("location")
    found_location = found.get("location")
    location_score = None
    known_locations = {
        "library",
        "canteen",
        "block a",
        "block b",
        "auditorium",
        "parking",
        "classroom",
    }
    if (
        _usable_text(lost_location)
        and _usable_text(found_location)
        and lost_location.strip().casefold() in known_locations
        and found_location.strip().casefold() in known_locations
    ):
        location_score = (
            100.0
            if lost_location.strip().casefold() == found_location.strip().casefold()
            else 0.0
        )

    model_error = get_semantic_model_error()
    if using_default_semantic_scorer and model_error and semantic_score is None:
        legacy_score = _valid_score(calculate_match_score(lost, found)) or 0.0
        return {
            "score": round(legacy_score, 2),
            "components": {"fuzzy": round(legacy_score, 2)},
            "reasons": ["Semantic model unavailable; using existing fuzzy matching"],
            "fallback": True,
            "fallback_reason": model_error,
        }

    components = {
        "fuzzy": fuzzy_score,
        "semantic": semantic_score,
        "image": image_score,
        "location": location_score,
    }
    available = [
        (configured_weights[name], score)
        for name, score in components.items()
        if score is not None and configured_weights[name] > 0
    ]
    total_weight = sum(weight for weight, _ in available)
    score = (
        sum(weight * value for weight, value in available) / total_weight
        if total_weight
        else 0.0
    )

    reasons = []
    if semantic_score is not None and semantic_score >= 60:
        reasons.append("Descriptions have similar meaning")
    if _valid_score(text_details.get("color")) == 100:
        reasons.append("Same color")
    if _valid_score(text_details.get("item_type")) == 100:
        reasons.append("Same item type")
    if _valid_score(text_details.get("brand")) == 100:
        reasons.append("Same brand")
    if image_score is not None and image_score >= 60:
        reasons.append("Photographs look similar")
    if location_score == 100:
        reasons.append("Same reported location")

    return {
        "score": round(score, 2),
        "components": {
            name: round(value, 2)
            for name, value in components.items()
            if value is not None
        },
        "reasons": reasons,
        "fallback": False,
    }


def get_hybrid_matches_for_lost(
    lost_item,
    found_items,
    threshold=60,
    weights=None,
    semantic_scorer=None,
    image_scorer=None,
):
    """Rank valid, unclaimed found reports and suppress duplicate records."""

    try:
        minimum_score = float(threshold)
    except (TypeError, ValueError):
        minimum_score = 60.0
    minimum_score = max(0.0, min(100.0, minimum_score))

    matches = []
    seen = set()
    for found in found_items if isinstance(found_items, list) else []:
        if not isinstance(found, dict):
            continue
        status = found.get("status", "Found")
        if isinstance(status, str) and status.strip().casefold() == "claimed":
            continue

        identifier = found.get("id")
        dedupe_key = (
            ("id", str(identifier))
            if identifier is not None
            else ("record", repr(sorted(found.items())))
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        result = calculate_hybrid_match(
            lost_item,
            found,
            weights=weights,
            semantic_scorer=semantic_scorer,
            image_scorer=image_scorer,
        )
        if result["score"] >= minimum_score:
            matches.append({
                "found": found,
                "score": result["score"],
                "result": (
                    "Strong Match" if result["score"] >= 80
                    else "Possible Match"
                ),
                "reasons": result["reasons"],
                "details": result["components"],
                "fallback": result["fallback"],
                "fallback_reason": result.get("fallback_reason"),
            })

    matches.sort(key=lambda match: match["score"], reverse=True)
    return matches