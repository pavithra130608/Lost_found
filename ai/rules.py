from datetime import datetime


def clean(value):
    """
    Convert a value to a clean lowercase string.
    """

    return str(value).strip().lower()


def check_date_proximity(lost_date, found_date):
    """
    Check whether the lost and found dates are reasonably close.

    Returns a human-readable explanation.
    """

    try:
        lost = datetime.strptime(
            lost_date,
            "%Y-%m-%d"
        ).date()

        found = datetime.strptime(
            found_date,
            "%Y-%m-%d"
        ).date()

        difference = abs(
            (lost - found).days
        )

        if difference == 0:
            return "Same date"

        elif difference <= 2:
            return "Dates are within 2 days"

        elif difference <= 7:
            return "Dates are within 1 week"

        else:
            return "Dates are more than 1 week apart"

    except (ValueError, TypeError):
        return None


def apply_rules(lost, found, score):
    """
    Apply rule-based inference to a lost/found item pair.

    Parameters:
        lost  -> lost item dictionary
        found -> found item dictionary
        score -> overall similarity score

    Returns:
        result  -> match category
        reasons -> list of explanations
    """

    reasons = []

    # -----------------------------------------
    # Clean values
    # -----------------------------------------

    lost_type = clean(
        lost.get("item_type", "")
    )

    found_type = clean(
        found.get("item_type", "")
    )

    lost_color = clean(
        lost.get("color", "")
    )

    found_color = clean(
        found.get("color", "")
    )

    lost_brand = clean(
        lost.get("brand", "")
    )

    found_brand = clean(
        found.get("brand", "")
    )

    lost_location = clean(
        lost.get("location", "")
    )

    found_location = clean(
        found.get("location", "")
    )

    # -----------------------------------------
    # Rule 1: Item Type
    # -----------------------------------------

    if lost_type and found_type:

        if lost_type == found_type:
            reasons.append(
                "Same item type"
            )

    # -----------------------------------------
    # Rule 2: Color
    # -----------------------------------------

    if lost_color and found_color:

        if lost_color == found_color:
            reasons.append(
                "Same color"
            )

    # -----------------------------------------
    # Rule 3: Brand
    # -----------------------------------------

    if lost_brand and found_brand:

        if lost_brand == found_brand:
            reasons.append(
                "Same brand"
            )

    # -----------------------------------------
    # Rule 4: Location
    # -----------------------------------------

    if lost_location and found_location:

        if lost_location == found_location:
            reasons.append(
                "Same location"
            )

        else:
            reasons.append(
                "Different reported locations"
            )

    # -----------------------------------------
    # Rule 5: Date Proximity
    # -----------------------------------------

    date_reason = check_date_proximity(
        lost.get("date", ""),
        found.get("date", "")
    )

    if date_reason:
        reasons.append(
            date_reason
        )

    # -----------------------------------------
    # Rule 6: Overall Similarity
    # -----------------------------------------

    if score >= 80:

        reasons.append(
            "High overall text similarity"
        )

    elif score >= 60:

        reasons.append(
            "Moderate overall text similarity"
        )

    else:

        reasons.append(
            "Low overall similarity"
        )

    # -----------------------------------------
    # Final Match Classification
    # -----------------------------------------

    if score >= 80:

        result = "Strong Match"

    elif score >= 60:

        result = "Possible Match"

    elif score >= 40:

        result = "Weak Match"

    else:

        result = "Unlikely Match"

    return result, reasons