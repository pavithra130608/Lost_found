import json

from ai.fuzzy_match import calculate_match_score
from ai.rules import apply_rules


# Load real lost items
with open("data/lost_items.json", "r") as file:
    lost_items = json.load(file)

# Load real found items
with open("data/found_items.json", "r") as file:
    found_items = json.load(file)


print("===== AI LOST & FOUND MATCHING TEST =====")

print("Lost Items:", len(lost_items))
print("Found Items:", len(found_items))


# Compare every lost item with every found item
for lost in lost_items:

    print("\n----------------------------------------")
    print("Lost Item ID:", lost["id"])
    print("Item:", lost["item_type"])
    print("Description:", lost["description"])

    for found in found_items:

        score = calculate_match_score(lost, found)

        result, reasons = apply_rules(
            lost,
            found,
            score
        )

        print("\nFound Item ID:", found["id"])
        print("Found Description:", found["description"])
        print("Match Score:", score)
        print("Result:", result)

        if reasons:
            print("Reasons:")
            for reason in reasons:
                print("  ✓", reason)