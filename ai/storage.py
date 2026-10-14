import json
import os


def load_items(filename):
    """Load dictionary records from a JSON list, tolerating malformed data."""

    if not os.path.exists(filename):
        return []

    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
    except (json.JSONDecodeError, OSError):
        pass
    return []


def save_items(filename, items):
    """Save item records as UTF-8 JSON, creating the parent folder if needed."""

    folder = os.path.dirname(filename)
    if folder:
        os.makedirs(folder, exist_ok=True)

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(items, file, indent=4, ensure_ascii=False)


def add_item(filename, item):
    """Append an item and assign the next available integer ID."""

    items = load_items(filename)
    existing_ids = []
    for existing_item in items:
        try:
            existing_ids.append(int(existing_item.get("id", 0)))
        except (ValueError, TypeError):
            continue

    item["id"] = max(existing_ids, default=0) + 1
    items.append(item)
    save_items(filename, items)


def update_item_status(filename, item_id, new_status):
    """Update a report status by integer-compatible ID."""

    try:
        requested_id = int(item_id)
    except (ValueError, TypeError):
        return False

    items = load_items(filename)
    for item in items:
        try:
            current_id = int(item.get("id", 0))
        except (ValueError, TypeError):
            continue
        if current_id == requested_id:
            item["status"] = new_status
            save_items(filename, items)
            return True
    return False