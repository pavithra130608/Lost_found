import json

from ai.item_match import find_item_matches


def main():
    with open("data/lost_items.json", "r", encoding="utf-8") as file:
        lost_items = json.load(file)

    with open("data/found_items.json", "r", encoding="utf-8") as file:
        found_items = json.load(file)

    print("===== LOST AND FOUND MATCHING CHECK =====")
    print("Lost Items:", len(lost_items))
    print("Found Items:", len(found_items))

    for lost in lost_items:
        matches, rejected = find_item_matches(lost, found_items)
        print("\n----------------------------------------")
        print(f"Lost Report {lost.get('id')}: {lost.get('item_type')}")
        print("Description:", lost.get("description", ""))

        if matches:
            for match in matches:
                found = match["found"]
                print(
                    f"Candidate Report {found.get('id')}: "
                    f"{found.get('item_type')} "
                    f"({match['score']:.0f}/100)"
                )
                for reason in match["reasons"]:
                    print("  -", reason)
        else:
            print("No credible candidate matches.")

        for entry in rejected:
            found = entry["found"]
            print(f"Rejected Report {found.get('id')}: {found.get('item_type')}")
            for reason in entry["reasons"]:
                print("  -", reason)


if __name__ == "__main__":
    main()