from math import ceil

def compute_shopping_list(
    recipe,
    unit_size,
    total_portions,
    event_date,
    donations,
):
    sandwich_count = unit_size * total_portions
    results = []

    for item, amount_per_sandwich in recipe.items():
        need = ceil(amount_per_sandwich * sandwich_count)
        usable_donations = 0
        needs_review = 0

        for donation in donations:
            if donation["item"] == item:
                if donation["expiry"] < event_date:
                    needs_review += donation["quantity"]
                else:
                    usable_donations += donation["quantity"]
        
        covered = min(need, usable_donations)
        to_buy = need - covered
        surplus = max(usable_donations - need, 0)
        results.append({
            "item": item,
            "need": need,
            "usable_donations": usable_donations,
            "needs_review": needs_review,
            "covered": covered,
            "to_buy": to_buy,
            "surplus": surplus,
        })
    return results