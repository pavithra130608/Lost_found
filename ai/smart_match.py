import html
import os
from ai.fuzzy_match import similarity
from ai.item_match import canonical_item_type, normalize_text
from ai.rules import check_date_proximity


def _format_list(items):
    """Format a list of strings with proper English commas and 'and'."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def get_smart_match_explanation(lost, found, match=None):
    """
    Evaluate and explain the similarity between a Lost and a Found report.

    Returns a dict with:
      - attributes: list of dicts with attribute comparison, status (Match, Partial Match, Different, Not Specified)
      - summary: concise summary sentence, e.g. 'Description and color match; brand differs.'
      - matches: list of matching attribute names
      - partials: list of partially matching attribute names
      - differs: list of differing attribute names
    """
    lost = lost or {}
    found = found or {}
    criteria = match.get("criteria", {}) if match else {}

    # ---------------------------------------------------------
    # 1. Category (Item Type)
    # ---------------------------------------------------------
    lost_type = str(lost.get("item_type", "")).strip()
    found_type = str(found.get("item_type", "")).strip()
    canon_lost = canonical_item_type(lost_type)
    canon_found = canonical_item_type(found_type)

    if not lost_type and not found_type:
        cat_status = "Not Specified"
        cat_note = "Item category was not specified in either report."
    elif not lost_type or not found_type:
        cat_status = "Different"
        cat_note = "Item category missing on one of the reports."
    elif canon_lost == canon_found:
        cat_status = "Match"
        if normalize_text(lost_type) == normalize_text(found_type):
            cat_note = f"Both reports are categorized as {lost_type}."
        else:
            cat_note = f"Compatible category synonyms: {lost_type} and {found_type}."
    else:
        cat_status = "Different"
        cat_note = f"Different item categories ({lost_type} vs {found_type})."

    # ---------------------------------------------------------
    # 2. Description
    # ---------------------------------------------------------
    lost_desc = str(lost.get("description", "")).strip()
    found_desc = str(found.get("description", "")).strip()

    if not lost_desc and not found_desc:
        desc_status = "Not Specified"
        desc_note = "No description provided in either report."
    elif not lost_desc or not found_desc:
        desc_status = "Different"
        desc_note = "Description is only present on one report."
    else:
        desc_score = (
            criteria.get("description")
            if "description" in criteria
            else round(similarity(normalize_text(lost_desc), normalize_text(found_desc)) * 100, 1)
        )
        if desc_score >= 70.0:
            desc_status = "Match"
            desc_note = f"Descriptions share strong similarity ({desc_score:.0f}% text similarity)."
        elif desc_score >= 25.0:
            desc_status = "Partial Match"
            desc_note = f"Descriptions share related wording ({desc_score:.0f}% text similarity)."
        else:
            desc_status = "Different"
            desc_note = f"Descriptions have little wording in common ({desc_score:.0f}% text similarity)."

    # ---------------------------------------------------------
    # 3. Brand
    # ---------------------------------------------------------
    lost_brand = str(lost.get("brand", "")).strip()
    found_brand = str(found.get("brand", "")).strip()

    if not lost_brand and not found_brand:
        brand_status = "Not Specified"
        brand_note = "Brand not specified on either report."
    elif not lost_brand or not found_brand:
        brand_status = "Different"
        brand_note = f"Brand specified on only one report ({lost_brand or found_brand})."
    else:
        brand_score = (
            criteria.get("brand")
            if "brand" in criteria
            else round(similarity(normalize_text(lost_brand), normalize_text(found_brand)) * 100, 1)
        )
        if brand_score >= 85.0:
            brand_status = "Match"
            brand_note = f"Same brand reported ({lost_brand})."
        elif brand_score >= 50.0:
            brand_status = "Partial Match"
            brand_note = f"Similar brand names ({lost_brand} vs {found_brand})."
        else:
            brand_status = "Different"
            brand_note = f"Different brands ({lost_brand} vs {found_brand})."

    # ---------------------------------------------------------
    # 4. Color
    # ---------------------------------------------------------
    lost_color = str(lost.get("color", "")).strip()
    found_color = str(found.get("color", "")).strip()

    if not lost_color and not found_color:
        color_status = "Not Specified"
        color_note = "Color not specified on either report."
    elif not lost_color or not found_color:
        color_status = "Different"
        color_note = f"Color specified on only one report ({lost_color or found_color})."
    else:
        norm_lost_col = normalize_text(lost_color)
        norm_found_col = normalize_text(found_color)
        if norm_lost_col == norm_found_col:
            color_status = "Match"
            color_note = f"Same color reported ({lost_color})."
        elif norm_lost_col in norm_found_col or norm_found_col in norm_lost_col:
            color_status = "Partial Match"
            color_note = f"Colors are related ({lost_color} vs {found_color})."
        else:
            color_status = "Different"
            color_note = f"Different colors ({lost_color} vs {found_color})."

    # ---------------------------------------------------------
    # 5. Location
    # ---------------------------------------------------------
    lost_loc = str(lost.get("location", "")).strip()
    found_loc = str(found.get("location", "")).strip()

    if not lost_loc and not found_loc:
        loc_status = "Not Specified"
        loc_note = "Location not specified on either report."
    elif not lost_loc or not found_loc:
        loc_status = "Different"
        loc_note = "Location specified on only one report."
    else:
        norm_lost_loc = normalize_text(lost_loc)
        norm_found_loc = normalize_text(found_loc)
        if norm_lost_loc == norm_found_loc:
            loc_status = "Match"
            loc_note = f"Reported at the same location ({lost_loc})."
        elif norm_lost_loc in norm_found_loc or norm_found_loc in norm_lost_loc:
            loc_status = "Partial Match"
            loc_note = f"Nearby or overlapping areas ({lost_loc} vs {found_loc})."
        else:
            loc_status = "Different"
            loc_note = f"Different reported locations ({lost_loc} vs {found_loc})."

    # ---------------------------------------------------------
    # 6. Date
    # ---------------------------------------------------------
    lost_date = str(lost.get("date", "")).strip()
    found_date = str(found.get("date", "")).strip()

    if not lost_date or not found_date:
        date_status = "Not Specified"
        date_note = "Date missing on one or both reports."
    else:
        proximity_note = check_date_proximity(lost_date, found_date)
        date_score = criteria.get("date")
        if date_score == 100.0 or proximity_note == "Same date":
            date_status = "Match"
            date_note = f"Reports have the same date ({lost_date})."
        elif date_score in (50.0, 75.0) or (proximity_note and "within" in proximity_note.lower()):
            date_status = "Partial Match"
            date_note = proximity_note or f"Close dates ({lost_date} and {found_date})."
        elif date_score == 25.0:
            date_status = "Partial Match"
            date_note = f"Dates within 30 days ({lost_date} vs {found_date})."
        else:
            date_status = "Different"
            date_note = proximity_note or f"Dates more than 30 days apart ({lost_date} vs {found_date})."

    # ---------------------------------------------------------
    # 7. Photo
    # ---------------------------------------------------------
    lost_img_path = lost.get("image_path")
    found_img_path = found.get("image_path")
    lost_has_photo = bool(lost_img_path and os.path.exists(lost_img_path))
    found_has_photo = bool(found_img_path and os.path.exists(found_img_path))
    photo_score = criteria.get("photo")

    if photo_score is not None:
        if photo_score >= 60.0:
            photo_status = "Match"
            photo_note = f"Photos are visually similar ({photo_score:.0f}% image similarity)."
        elif photo_score >= 35.0:
            photo_status = "Partial Match"
            photo_note = f"Moderate visual similarity ({photo_score:.0f}% image similarity)."
        else:
            photo_status = "Different"
            photo_note = f"Photos differ visually ({photo_score:.0f}% image similarity)."
    elif lost_has_photo and not found_has_photo:
        photo_status = "Not Specified"
        photo_note = "Photo uploaded on Lost report only."
    elif not lost_has_photo and found_has_photo:
        photo_status = "Not Specified"
        photo_note = "Photo uploaded on Found report only."
    else:
        photo_status = "Not Specified"
        photo_note = "No photos uploaded."

    attributes = [
        {
            "name": "Category",
            "lost": lost_type or "Not specified",
            "found": found_type or "Not specified",
            "status": cat_status,
            "note": cat_note,
        },
        {
            "name": "Description",
            "lost": lost_desc or "Not specified",
            "found": found_desc or "Not specified",
            "status": desc_status,
            "note": desc_note,
        },
        {
            "name": "Brand",
            "lost": lost_brand or "Not specified",
            "found": found_brand or "Not specified",
            "status": brand_status,
            "note": brand_note,
        },
        {
            "name": "Color",
            "lost": lost_color or "Not specified",
            "found": found_color or "Not specified",
            "status": color_status,
            "note": color_note,
        },
        {
            "name": "Location",
            "lost": lost_loc or "Not specified",
            "found": found_loc or "Not specified",
            "status": loc_status,
            "note": loc_note,
        },
        {
            "name": "Date",
            "lost": lost_date or "Not specified",
            "found": found_date or "Not specified",
            "status": date_status,
            "note": date_note,
        },
        {
            "name": "Photo",
            "lost": "Photo attached" if lost_has_photo else "No photo",
            "found": "Photo attached" if found_has_photo else "No photo",
            "status": photo_status,
            "note": photo_note,
        },
    ]

    # ---------------------------------------------------------
    # Natural Language Summary Synthesis
    # ---------------------------------------------------------
    matches = [a["name"] for a in attributes if a["status"] == "Match"]
    partials = [a["name"] for a in attributes if a["status"] == "Partial Match"]
    differs = [a["name"] for a in attributes if a["status"] == "Different"]

    clauses = []
    if matches:
        verb = "match" if len(matches) > 1 else "matches"
        clauses.append(f"{_format_list([m.lower() for m in matches])} {verb}")
    if partials:
        verb = "partially match" if len(partials) > 1 else "partially matches"
        clauses.append(f"{_format_list([p.lower() for p in partials])} {verb}")
    if differs:
        verb = "differ" if len(differs) > 1 else "differs"
        clauses.append(f"{_format_list([d.lower() for d in differs])} {verb}")

    if clauses:
        summary = "; ".join(clauses).capitalize() + "."
    else:
        summary = "No matching or differing attributes identified."

    return {
        "summary": summary,
        "attributes": attributes,
        "matches": matches,
        "partials": partials,
        "differs": differs,
    }


def render_smart_match_summary_html(explanation):
    """Generate a clean styled summary card without leading indentation."""
    summary_text = html.escape(str(explanation.get("summary", "")))
    return (
        '<div style="background:#eef6f2;border-left:4px solid #17463c;'
        'padding:0.75rem 1rem;border-radius:6px;margin:0.25rem 0 0.85rem;color:#17463c;">'
        '<div style="font-size:0.75rem;text-transform:uppercase;font-weight:700;'
        'letter-spacing:0.5px;color:#28584c;margin-bottom:2px;">Smart Match Summary</div>'
        f'<div style="font-size:1.02rem;font-weight:600;">💡 {summary_text}</div>'
        '</div>'
    )


def render_smart_match_html(explanation):
    """Generate an accessible, styled HTML table comparing attributes with badges without leading whitespace."""
    badge_styles = {
        "Match": "background:#dff1e7;color:#10593b;border:1px solid #b6dec9;",
        "Partial Match": "background:#fff0d4;color:#8a5800;border:1px solid #f6d499;",
        "Different": "background:#fde8e4;color:#b83a24;border:1px solid #f5b8ad;",
        "Not Specified": "background:#edf2f0;color:#65766f;border:1px solid #d4ded9;",
    }
    badge_icons = {
        "Match": "🟢",
        "Partial Match": "🟡",
        "Different": "🔴",
        "Not Specified": "⚪",
    }

    rows_html = []
    for attr in explanation["attributes"]:
        status = attr["status"]
        style = badge_styles.get(status, badge_styles["Not Specified"])
        icon = badge_icons.get(status, "⚪")
        badge = (
            f'<span style="{style}padding:3px 9px;border-radius:12px;'
            f'font-weight:700;font-size:0.8rem;white-space:nowrap;">'
            f'{icon} {html.escape(status)}</span>'
        )

        name_esc = html.escape(str(attr.get("name", "")))
        lost_esc = html.escape(str(attr.get("lost", "")))
        found_esc = html.escape(str(attr.get("found", "")))
        note_esc = html.escape(str(attr.get("note", "")))

        rows_html.append(
            f'<tr style="border-bottom:1px solid #e1ebe5;">'
            f'<td style="padding:8px 10px;font-weight:600;color:#17463c;">{name_esc}</td>'
            f'<td style="padding:8px 10px;color:#20342e;max-width:180px;word-break:break-word;">{lost_esc}</td>'
            f'<td style="padding:8px 10px;color:#20342e;max-width:180px;word-break:break-word;">{found_esc}</td>'
            f'<td style="padding:8px 10px;">{badge}</td>'
            f'<td style="padding:8px 10px;color:#52665e;font-size:0.86rem;">{note_esc}</td>'
            f'</tr>'
        )

    table_body = "".join(rows_html)

    return (
        f'<div style="margin:0.75rem 0 1rem;overflow-x:auto;">'
        f'<table style="width:100%;border-collapse:collapse;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif;font-size:0.9rem;background:#ffffff;border:1px solid #d8e3dd;border-radius:8px;">'
        f'<thead><tr style="background:#f3f7f4;border-bottom:2px solid #cbd9d1;text-align:left;color:#17463c;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.4px;">'
        f'<th style="padding:8px 10px;">Attribute</th>'
        f'<th style="padding:8px 10px;">Lost Report</th>'
        f'<th style="padding:8px 10px;">Found Report</th>'
        f'<th style="padding:8px 10px;">Status</th>'
        f'<th style="padding:8px 10px;">Details</th>'
        f'</tr></thead>'
        f'<tbody>{table_body}</tbody>'
        f'</table>'
        f'<div style="font-size:0.78rem;color:#65766f;margin-top:6px;">'
        f'ℹ️ Match rating reflects attribute similarity criteria; it is not proof of ownership.'
        f'</div>'
        f'</div>'
    )
