from math import ceil

def split_ingredient(total_quantity, volunteer_count):
    """
    Divide an ingredient as evenly as possible.
    Any remainder goes to the first volunteers.
    """
    if volunteer_count < 1:
        return []

    base_amount = total_quantity // volunteer_count
    remainder = total_quantity % volunteer_count

    shares = []

    for index in range(volunteer_count):
        amount = base_amount

        if index < remainder:
            amount += 1

        shares.append(amount)

    return shares

def make_kits(signups, recipe, unit_size):
    """
    Build one ingredient kit per signup.
    Each portion represents unit_size sandwiches.
    """
    kits = []

    for signup in signups:
        sandwich_count = signup["portions"] * unit_size
        ingredients = {}

        for item, amount_per_sandwich in recipe.items():
            ingredients[item] = ceil(amount_per_sandwich * sandwich_count)

        kits.append({
            "first_name": signup["first_name"],
            "portions": signup["portions"],
            "signup_id": signup["signup_id"],
            "ingredients": ingredients,
        })

    return kits

def allocate_donations(kits, donations, event_date):
    """
    Allocate usable donations to kits by earliest expiration date.
    Expired donations are not allocated.
    Any shortage is marked as an amount to buy.
    """
    remaining_donations = [
        {
            "item": donation["item"],
            "quantity": donation["quantity"],
            "expiry": donation["expiry"],
        }
        for donation in donations
        if donation["expiry"] >= event_date
    ]

    remaining_donations.sort(key=lambda donation: donation["expiry"])

    allocated_kits = []

    for index, kit in enumerate(kits, start=1):
        ingredient_plan = {}

        for item, needed in kit["ingredients"].items():
            still_needed = needed
            donated_lots = []

            for donation in remaining_donations:
                if donation["item"] != item or donation["quantity"] == 0:
                    continue

                amount = min(still_needed, donation["quantity"])

                if amount > 0:
                    donated_lots.append({
                        "quantity": amount,
                        "expiry": donation["expiry"],
                    })
                    donation["quantity"] -= amount
                    still_needed -= amount

                if still_needed == 0:
                    break

            ingredient_plan[item] = {
                "needed": needed,
                "donated": donated_lots,
                "to_buy": still_needed,
            }

        allocated_kits.append({
            "volunteer": f"Volunteer {index}",
            "portions": kit["portions"],
            "signup_id": kit["signup_id"],
            "ingredients": ingredient_plan,
        })

    return allocated_kits