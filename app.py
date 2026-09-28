import streamlit as st
import json
import os
from datetime import date

from ai.fuzzy_match import (
    calculate_match_score,
    calculate_match_details
)

from ai.rules import apply_rules


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AI Lost & Found",
    page_icon="🔎",
    layout="wide"
)


# =========================================================
# FILE PATHS
# =========================================================

LOST_FILE = "data/lost_items.json"
FOUND_FILE = "data/found_items.json"


# =========================================================
# DATA FUNCTIONS
# =========================================================

def load_items(filename):
    """Load items from JSON file."""

    if not os.path.exists(filename):
        return []

    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

        return []

    except (json.JSONDecodeError, OSError):
        return []


def save_items(filename, items):
    """Save items to JSON file."""

    folder = os.path.dirname(filename)

    if folder:
        os.makedirs(folder, exist_ok=True)

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(
            items,
            file,
            indent=4,
            ensure_ascii=False
        )


def add_item(filename, item):
    """Add a new item and automatically generate an ID."""

    items = load_items(filename)

    existing_ids = []

    for existing_item in items:

        try:
            existing_ids.append(
                int(existing_item.get("id", 0))
            )

        except (ValueError, TypeError):
            pass

    item["id"] = max(
        existing_ids,
        default=0
    ) + 1

    items.append(item)

    save_items(
        filename,
        items
    )


def update_item_status(filename, item_id, new_status):
    """Update status of an item."""

    items = load_items(filename)

    updated = False

    for item in items:

        try:
            current_id = int(
                item.get("id", 0)
            )

        except (ValueError, TypeError):
            continue

        if current_id == int(item_id):

            item["status"] = new_status
            updated = True
            break

    if updated:

        save_items(
            filename,
            items
        )

    return updated


# =========================================================
# MATCHING FUNCTIONS
# =========================================================

def get_matches_for_lost(lost_item, found_items):
    """
    Find all available found items that match
    the selected lost item.
    """

    matches = []

    for found in found_items:

        if found.get("status", "Found") == "Claimed":
            continue

        score = calculate_match_score(
            lost_item,
            found
        )

        if score >= 60:

            details = calculate_match_details(
                lost_item,
                found
            )

            result, reasons = apply_rules(
                lost_item,
                found,
                score
            )

            matches.append({
                "found": found,
                "score": score,
                "result": result,
                "reasons": reasons,
                "details": details
            })

    matches.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return matches


def count_all_matches(lost_items, found_items):
    """Count all possible matches."""

    count = 0

    for lost in lost_items:

        matches = get_matches_for_lost(
            lost,
            found_items
        )

        count += len(matches)

    return count


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 18px;
        opacity: 0.75;
        margin-bottom: 25px;
    }

    .action-card {
        padding: 24px;
        border: 1px solid rgba(128,128,128,0.25);
        border-radius: 14px;
        margin-bottom: 10px;
    }

    .section-title {
        font-size: 27px;
        font-weight: 650;
        margin-top: 20px;
        margin-bottom: 15px;
    }

    .status-lost {
        padding: 5px 12px;
        border-radius: 20px;
        background-color: rgba(255, 193, 7, 0.15);
        display: inline-block;
    }

    .status-found {
        padding: 5px 12px;
        border-radius: 20px;
        background-color: rgba(33, 150, 243, 0.15);
        display: inline-block;
    }

    .status-claimed {
        padding: 5px 12px;
        border-radius: 20px;
        background-color: rgba(76, 175, 80, 0.15);
        display: inline-block;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("🔎 AI Lost & Found")

st.sidebar.caption(
    "Find what you've lost. Return what you've found."
)

st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    [
        "Home",
        "Report Lost",
        "Report Found",
        "Possible Matches",
        "Reports"
    ]
)

st.sidebar.divider()

st.sidebar.caption(
    "AI matching works automatically in the background."
)


# =========================================================
# HOME
# =========================================================

if page == "Home":

    lost_items = load_items(LOST_FILE)
    found_items = load_items(FOUND_FILE)

    active_found = [
        item
        for item in found_items
        if item.get("status", "Found") != "Claimed"
    ]

    claimed_items = [
        item
        for item in found_items
        if item.get("status") == "Claimed"
    ]

    total_matches = count_all_matches(
        lost_items,
        found_items
    )

    # =====================================================
    # HERO
    # =====================================================

    st.markdown(
        '<div class="main-title">🔎 AI Lost & Found</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Find what you\'ve lost. Return what you\'ve found.'
        '</div>',
        unsafe_allow_html=True
    )

    # =====================================================
    # QUICK ACTIONS
    # =====================================================

    st.markdown(
        '<div class="section-title">What would you like to do?</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            """
            <div class="action-card">
                <h3>📢 I Lost Something</h3>
                <p>
                    Report an item you lost and let the
                    system look for possible matches.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "📢 Report Lost Item",
            use_container_width=True
        ):

            st.info(
                "Use 'Report Lost' from the sidebar."
            )

    with col2:

        st.markdown(
            """
            <div class="action-card">
                <h3>📦 I Found Something</h3>
                <p>
                    Report an item you found so its owner
                    can discover it.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "📦 Report Found Item",
            use_container_width=True
        ):

            st.info(
                "Use 'Report Found' from the sidebar."
            )

    st.divider()

    # =====================================================
    # STATISTICS
    # =====================================================

    st.markdown(
        '<div class="section-title">📊 Current Activity</div>',
        unsafe_allow_html=True
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "📢 Lost",
            len(lost_items)
        )

    with col2:

        st.metric(
            "📦 Found",
            len(active_found)
        )

    with col3:

        st.metric(
            "🎯 Possible Matches",
            total_matches
        )

    with col4:

        st.metric(
            "✅ Claimed",
            len(claimed_items)
        )

    st.divider()

    # =====================================================
    # POSSIBLE MATCHES
    # =====================================================

    st.markdown(
        '<div class="section-title">🎯 Possible Matches</div>',
        unsafe_allow_html=True
    )

    all_matches = []

    for lost in lost_items:

        matches = get_matches_for_lost(
            lost,
            found_items
        )

        for match in matches:

            all_matches.append({
                "lost": lost,
                "match": match
            })

    all_matches.sort(
        key=lambda x: x["match"]["score"],
        reverse=True
    )

    if not all_matches:

        st.success(
            "No possible matches right now."
        )

        st.write(
            "When a matching found item is reported, "
            "it will appear here automatically."
        )

    else:

        st.write(
            "We found items that may correspond to "
            "reported lost items."
        )

        # Display only top 3 on dashboard
        for index, item_data in enumerate(
            all_matches[:3]
        ):

            lost = item_data["lost"]
            match = item_data["match"]
            found = match["found"]

            with st.container(border=True):

                col1, col2, col3 = st.columns(
                    [2.5, 2.5, 1]
                )

                with col1:

                    st.markdown(
                        "### 📢 Lost"
                    )

                    st.write(
                        f"**{lost.get('item_type', 'Item')}**"
                    )

                    st.write(
                        f"📍 {lost.get('location', 'Unknown')}"
                    )

                    st.write(
                        f"📅 {lost.get('date', 'Unknown')}"
                    )

                with col2:

                    st.markdown(
                        "### 📦 Found"
                    )

                    st.write(
                        f"**{found.get('item_type', 'Item')}**"
                    )

                    st.write(
                        f"📍 {found.get('location', 'Unknown')}"
                    )

                    st.write(
                        f"📅 {found.get('date', 'Unknown')}"
                    )

                with col3:

                    st.metric(
                        "Match",
                        f"{match['score']}%"
                    )

                    if match["score"] >= 80:

                        st.success(
                            "Strong"
                        )

                    else:

                        st.warning(
                            "Possible"
                        )

    if len(all_matches) > 3:

        st.caption(
            f"{len(all_matches) - 3} more possible "
            "match(es) available."
        )

    st.divider()

    # =====================================================
    # RECENT ACTIVITY
    # =====================================================

    st.markdown(
        '<div class="section-title">🕒 Recent Activity</div>',
        unsafe_allow_html=True
    )

    recent_items = []

    for item in lost_items:

        recent_items.append({
            "type": "lost",
            "item": item
        })

    for item in found_items:

        recent_items.append({
            "type": "found",
            "item": item
        })

    # Sort by date where possible
    recent_items.sort(
        key=lambda x: x["item"].get("date", ""),
        reverse=True
    )

    if not recent_items:

        st.info(
            "No reports have been submitted yet."
        )

    else:

        for activity in recent_items[:5]:

            item = activity["item"]

            if activity["type"] == "lost":

                st.write(
                    f"📢 **{item.get('item_type', 'Item')}** "
                    f"was reported as lost on "
                    f"{item.get('date', '')}."
                )

            else:

                status = item.get(
                    "status",
                    "Found"
                )

                if status == "Claimed":

                    st.write(
                        f"✅ **{item.get('item_type', 'Item')}** "
                        f"was claimed."
                    )

                else:

                    st.write(
                        f"📦 **{item.get('item_type', 'Item')}** "
                        f"was reported as found on "
                        f"{item.get('date', '')}."
                    )


# =========================================================
# REPORT LOST
# =========================================================

elif page == "Report Lost":

    st.title("📢 Report Lost Item")

    st.write(
        "Tell us about the item you lost."
    )

    st.divider()

    with st.form("lost_item_form"):

        col1, col2 = st.columns(2)

        with col1:

            item_type = st.selectbox(
                "Item Type",
                [
                    "Backpack",
                    "Wallet",
                    "Phone",
                    "Keys",
                    "ID Card",
                    "Laptop",
                    "Bottle",
                    "Book",
                    "Other"
                ]
            )

            color = st.text_input(
                "Color",
                placeholder="Example: Black"
            )

            brand = st.text_input(
                "Brand",
                placeholder="Example: Nike"
            )

            location = st.selectbox(
                "Where did you lose it?",
                [
                    "Library",
                    "Canteen",
                    "Block A",
                    "Block B",
                    "Auditorium",
                    "Parking",
                    "Classroom",
                    "Other"
                ]
            )

        with col2:

            lost_date = st.date_input(
                "Date Lost",
                value=date.today()
            )

            name = st.text_input(
                "Your Name",
                placeholder="Enter your name"
            )

            description = st.text_area(
                "Description",
                placeholder=(
                    "Describe the item in detail..."
                ),
                height=150
            )

        submitted = st.form_submit_button(
            "📢 Submit Lost Report",
            use_container_width=True
        )

    if submitted:

        if not name.strip():

            st.warning(
                "Please enter your name."
            )

        elif not description.strip():

            st.warning(
                "Please enter a description."
            )

        else:

            new_item = {
                "item_type": item_type,
                "color": color.strip(),
                "brand": brand.strip(),
                "location": location,
                "date": str(lost_date),
                "name": name.strip(),
                "description": description.strip(),
                "status": "Lost"
            }

            add_item(
                LOST_FILE,
                new_item
            )

            st.success(
                "✅ Your lost item has been reported."
            )

            st.info(
                "We'll compare it automatically with "
                "available found items."
            )

            st.rerun()


# =========================================================
# REPORT FOUND
# =========================================================

elif page == "Report Found":

    st.title("📦 Report Found Item")

    st.write(
        "Tell us about the item you found."
    )

    st.divider()

    with st.form("found_item_form"):

        col1, col2 = st.columns(2)

        with col1:

            item_type = st.selectbox(
                "Item Type",
                [
                    "Backpack",
                    "Wallet",
                    "Phone",
                    "Keys",
                    "ID Card",
                    "Laptop",
                    "Bottle",
                    "Book",
                    "Other"
                ]
            )

            color = st.text_input(
                "Color",
                placeholder="Example: Black"
            )

            brand = st.text_input(
                "Brand",
                placeholder="Example: Nike"
            )

            location = st.selectbox(
                "Where did you find it?",
                [
                    "Library",
                    "Canteen",
                    "Block A",
                    "Block B",
                    "Auditorium",
                    "Parking",
                    "Classroom",
                    "Other"
                ]
            )

        with col2:

            found_date = st.date_input(
                "Date Found",
                value=date.today()
            )

            name = st.text_input(
                "Your Name",
                placeholder="Enter your name"
            )

            description = st.text_area(
                "Description",
                placeholder=(
                    "Describe the item and where you found it..."
                ),
                height=150
            )

        submitted = st.form_submit_button(
            "📦 Submit Found Report",
            use_container_width=True
        )

    if submitted:

        if not name.strip():

            st.warning(
                "Please enter your name."
            )

        elif not description.strip():

            st.warning(
                "Please enter a description."
            )

        else:

            new_item = {
                "item_type": item_type,
                "color": color.strip(),
                "brand": brand.strip(),
                "location": location,
                "date": str(found_date),
                "name": name.strip(),
                "description": description.strip(),
                "status": "Found"
            }

            add_item(
                FOUND_FILE,
                new_item
            )

            st.success(
                "✅ Your found item has been reported."
            )

            st.info(
                "The item is now available for matching."
            )

            st.rerun()


# =========================================================
# POSSIBLE MATCHES
# =========================================================

elif page == "Possible Matches":

    st.title("🎯 Possible Matches")

    st.write(
        "Check items that may correspond to something "
        "you reported as lost."
    )

    st.divider()

    lost_items = load_items(LOST_FILE)
    found_items = load_items(FOUND_FILE)

    available_found_items = [
        item
        for item in found_items
        if item.get("status", "Found") != "Claimed"
    ]

    if not lost_items:

        st.info(
            "No lost items have been reported yet."
        )

    elif not available_found_items:

        st.info(
            "There are no available found items yet."
        )

    else:

        # =================================================
        # SELECT LOST ITEM
        # =================================================

        lost_options = []

        for lost in lost_items:

            label = (
                f"ID {lost.get('id')} | "
                f"{lost.get('item_type', '')} | "
                f"{lost.get('color', '')} | "
                f"{lost.get('location', '')}"
            )

            lost_options.append(label)

        selected_lost = st.selectbox(
            "Select a lost item",
            lost_options
        )

        selected_index = lost_options.index(
            selected_lost
        )

        selected_lost_item = lost_items[
            selected_index
        ]

        # =================================================
        # SELECTED LOST ITEM
        # =================================================

        with st.container(border=True):

            st.markdown(
                "### 📢 Your Lost Item"
            )

            col1, col2 = st.columns(2)

            with col1:

                st.write(
                    f"**Type:** "
                    f"{selected_lost_item.get('item_type', '')}"
                )

                st.write(
                    f"**Color:** "
                    f"{selected_lost_item.get('color', '')}"
                )

                st.write(
                    f"**Brand:** "
                    f"{selected_lost_item.get('brand', '')}"
                )

            with col2:

                st.write(
                    f"**Location:** "
                    f"{selected_lost_item.get('location', '')}"
                )

                st.write(
                    f"**Date:** "
                    f"{selected_lost_item.get('date', '')}"
                )

                st.write(
                    f"**Description:** "
                    f"{selected_lost_item.get('description', '')}"
                )

        st.divider()

        # =================================================
        # FIND MATCHES
        # =================================================

        matches = get_matches_for_lost(
            selected_lost_item,
            available_found_items
        )

        if not matches:

            st.warning(
                "No possible matches were found."
            )

            st.write(
                "We'll show a match here when a sufficiently "
                "similar found item is available."
            )

        else:

            st.subheader(
                f"🔎 {len(matches)} Possible Match"
                + ("es" if len(matches) != 1 else "")
            )

            for match_index, match in enumerate(matches):

                found = match["found"]
                score = match["score"]

                with st.container(border=True):

                    # -------------------------------------
                    # Match header
                    # -------------------------------------

                    if score >= 80:

                        st.markdown(
                            "### 🟢 Strong Match"
                        )

                    else:

                        st.markdown(
                            "### 🟡 Possible Match"
                        )

                    col1, col2 = st.columns(
                        [3, 1]
                    )

                    with col1:

                        st.write(
                            f"**Item:** "
                            f"{found.get('item_type', '')}"
                        )

                        st.write(
                            f"**Color:** "
                            f"{found.get('color', 'Not specified')}"
                        )

                        st.write(
                            f"**Brand:** "
                            f"{found.get('brand', 'Not specified')}"
                        )

                        st.write(
                            f"**Location:** "
                            f"{found.get('location', '')}"
                        )

                        st.write(
                            f"**Date Found:** "
                            f"{found.get('date', '')}"
                        )

                        st.write(
                            f"**Description:** "
                            f"{found.get('description', '')}"
                        )

                    with col2:

                        st.metric(
                            "Match Score",
                            f"{score}%"
                        )

                        st.write(
                            f"Reported by: "
                            f"**{found.get('name', 'Unknown')}**"
                        )

                    # -------------------------------------
                    # AI explanation
                    # -------------------------------------

                    st.divider()

                    with st.expander(
                        "🧠 Why is this a possible match?"
                    ):

                        details = match["details"]

                        st.write(
                            "The system compared the details "
                            "of your lost item with this found item."
                        )

                        # Safely display details
                        if isinstance(details, dict):

                            for key, value in details.items():

                                label = key.replace(
                                    "_",
                                    " "
                                ).title()

                                try:
                                    display_value = f"{float(value):.0f}%"
                                except (ValueError, TypeError):
                                    display_value = str(value)

                                st.write(
                                    f"**{label}:** "
                                    f"{display_value}"
                                )

                        st.markdown(
                            "#### Matching factors"
                        )

                        if match["reasons"]:

                            for reason in match["reasons"]:

                                st.write(
                                    f"✓ {reason}"
                                )

                        else:

                            st.write(
                                "No additional matching factors."
                            )

                    # -------------------------------------
                    # Claim
                    # -------------------------------------

                    st.divider()

                    if st.button(
                        "✅ Claim This Item",
                        key=f"claim_{found.get('id')}_{match_index}",
                        use_container_width=True
                    ):

                        success = update_item_status(
                            FOUND_FILE,
                            found.get("id"),
                            "Claimed"
                        )

                        if success:

                            st.success(
                                "✅ Item marked as claimed."
                            )

                            st.rerun()

                        else:

                            st.error(
                                "Unable to update the item."
                            )


# =========================================================
# REPORTS
# =========================================================

elif page == "Reports":

    st.title("📋 Reports")

    st.write(
        "View all lost and found reports in the system."
    )

    st.divider()

    lost_items = load_items(LOST_FILE)
    found_items = load_items(FOUND_FILE)

    # =====================================================
    # SUMMARY
    # =====================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "📢 Lost Reports",
            len(lost_items)
        )

    with col2:

        st.metric(
            "📦 Found Reports",
            len(found_items)
        )

    with col3:

        claimed_count = sum(
            1
            for item in found_items
            if item.get("status") == "Claimed"
        )

        st.metric(
            "✅ Claimed",
            claimed_count
        )

    st.divider()

    # =====================================================
    # LOST REPORTS
    # =====================================================

    st.subheader("📢 Lost Reports")

    if not lost_items:

        st.info(
            "No lost reports available."
        )

    else:

        for lost in lost_items:

            with st.container(border=True):

                col1, col2 = st.columns(
                    [4, 1]
                )

                with col1:

                    st.markdown(
                        f"### 📢 "
                        f"{lost.get('item_type', 'Item')}"
                    )

                    st.write(
                        f"**Report ID:** "
                        f"{lost.get('id', '')}"
                    )

                    st.write(
                        f"**Color:** "
                        f"{lost.get('color', 'Not specified')}"
                    )

                    st.write(
                        f"**Brand:** "
                        f"{lost.get('brand', 'Not specified')}"
                    )

                    st.write(
                        f"**Location:** "
                        f"{lost.get('location', '')}"
                    )

                    st.write(
                        f"**Date:** "
                        f"{lost.get('date', '')}"
                    )

                    st.write(
                        f"**Reported by:** "
                        f"{lost.get('name', '')}"
                    )

                    st.write(
                        f"**Description:** "
                        f"{lost.get('description', '')}"
                    )

                with col2:

                    st.markdown(
                        "#### Status"
                    )

                    st.warning(
                        "📢 Lost"
                    )

                    matches = get_matches_for_lost(
                        lost,
                        found_items
                    )

                    if matches:

                        st.info(
                            f"🎯 {len(matches)} "
                            "possible match(es)"
                        )

                    else:

                        st.caption(
                            "No match yet"
                        )

    # =====================================================
    # FOUND REPORTS
    # =====================================================

    st.divider()

    st.subheader("📦 Found Reports")

    if not found_items:

        st.info(
            "No found reports available."
        )

    else:

        for found in found_items:

            with st.container(border=True):

                col1, col2 = st.columns(
                    [4, 1]
                )

                with col1:

                    st.markdown(
                        f"### 📦 "
                        f"{found.get('item_type', 'Item')}"
                    )

                    st.write(
                        f"**Report ID:** "
                        f"{found.get('id', '')}"
                    )

                    st.write(
                        f"**Color:** "
                        f"{found.get('color', 'Not specified')}"
                    )

                    st.write(
                        f"**Brand:** "
                        f"{found.get('brand', 'Not specified')}"
                    )

                    st.write(
                        f"**Location:** "
                        f"{found.get('location', '')}"
                    )

                    st.write(
                        f"**Date:** "
                        f"{found.get('date', '')}"
                    )

                    st.write(
                        f"**Reported by:** "
                        f"{found.get('name', '')}"
                    )

                    st.write(
                        f"**Description:** "
                        f"{found.get('description', '')}"
                    )

                with col2:

                    st.markdown(
                        "#### Status"
                    )

                    status = found.get(
                        "status",
                        "Found"
                    )

                    if status == "Claimed":

                        st.success(
                            "✅ Claimed"
                        )

                    else:

                        st.info(
                            "📦 Found"
                        )

                        # Check whether this found item
                        # matches any lost item

                        possible_matches = 0

                        for lost in lost_items:

                            score = calculate_match_score(
                                lost,
                                found
                            )

                            if score >= 60:

                                possible_matches += 1

                        if possible_matches:

                            st.info(
                                f"🎯 {possible_matches} "
                                "possible match(es)"
                            )

                        else:

                            st.caption(
                                "No match yet"
                            )