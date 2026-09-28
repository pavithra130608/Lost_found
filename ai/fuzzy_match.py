from difflib import SequenceMatcher


def similarity(text1, text2):
    """
    Calculate text similarity between 0 and 1.
    """

    text1 = str(text1).lower().strip()
    text2 = str(text2).lower().strip()

    if not text1 or not text2:
        return 0.0

    return SequenceMatcher(None, text1, text2).ratio()


def calculate_match_details(lost, found):
    """
    Calculate similarity for each attribute
    and the overall weighted match score.
    """

    type_score = similarity(
        lost.get("item_type", ""),
        found.get("item_type", "")
    )

    color_score = similarity(
        lost.get("color", ""),
        found.get("color", "")
    )

    brand_score = similarity(
        lost.get("brand", ""),
        found.get("brand", "")
    )

    location_score = similarity(
        lost.get("location", ""),
        found.get("location", "")
    )

    description_score = similarity(
        lost.get("description", ""),
        found.get("description", "")
    )

    # -----------------------------------------
    # Weights
    # -----------------------------------------

    type_weight = 25
    color_weight = 15
    brand_weight = 15
    location_weight = 20
    description_weight = 25

    # -----------------------------------------
    # Overall score
    # -----------------------------------------

    overall_score = (
        type_score * type_weight
        + color_score * color_weight
        + brand_score * brand_weight
        + location_score * location_weight
        + description_score * description_weight
    )

    return {
        "item_type": round(type_score * 100, 2),
        "color": round(color_score * 100, 2),
        "brand": round(brand_score * 100, 2),
        "location": round(location_score * 100, 2),
        "description": round(description_score * 100, 2),
        "overall": round(overall_score, 2)
    }


def calculate_match_score(lost, found):
    """
    Return only the overall match score.
    """

    details = calculate_match_details(
        lost,
        found
    )

    return details["overall"]


def get_match_level(score):
    """
    Convert the score into a match category.
    """

    if score >= 80:
        return "Strong Match"

    elif score >= 60:
        return "Possible Match"

    elif score >= 40:
        return "Weak Match"

    else:
        return "Unlikely Match"