from datetime import date

import streamlit as st

from db import (
    add_signup,
    initialize_database,
    load_donations,
    load_signups,
    replace_donations,
)

from core.planner import compute_shopping_list

from core.kit_splitter import make_kits, allocate_donations

initialize_database()

target_portions = 9
signups = load_signups()
signed_portions = sum(signup["portions"] for signup in signups)
remaining_portions = target_portions - signed_portions

st.subheader("Volunteer sign-up")
st.write(f"Signed up: {signed_portions} / {target_portions} portions")
st.write(f"Remaining: {remaining_portions} portions")

if remaining_portions > 0:
    with st.form("signup_form"):
        first_name = st.text_input("First name")
        pin = st.text_input("Choose a 4-digit PIN", type="password")
        portions = st.number_input(
            "Portions to sign up for",
            min_value=1,
            max_value=remaining_portions,
            value=1,
            step=1,
        )
        submitted = st.form_submit_button("Sign up")

    if submitted:
        success, message = add_signup(
            first_name=first_name,
            pin=pin,
            portions=int(portions),
            target_portions=target_portions,
        )
        if success:
            st.success(message)
            st.rerun()
        else:
            st.error(message)
else:
    st.info("The signup target has been reached.")

if signups:
    st.subheader("Signup summary")
    signup_summary = [
        {
            "Volunteer": f"Volunteer {index}",
            "Portions": signup["portions"],
        }
        for index, signup in enumerate(signups, start=1)
    ]
    st.dataframe(signup_summary, hide_index=True)

saved_donations = {
    donation["item"]: donation
    for donation in load_donations()
}

st.title("Sandwich Angels")
st.write("Plan ingredients for the next sandwich volunteer event.")

recipe = {
    "bread_slices": 2,
    "ham_slices": 1,
    "cheese_slices": 1,
    "lettuce_bags": 1 / 30,
    "pickle_small_jars": 1 / 30,
    "mustard_small_bottles": 1 / 30,
    "mayonnaise_small_bottles": 1 / 30,
}
unit_size = 10

event_date = st.date_input(
    "Event date",
    value=date(2026, 10, 30),
)

total_portions = signed_portions
st.write(f"Portions used for shopping list: {total_portions}")

st.subheader("Donations")

bread_quantity = st.number_input(
    "Bread donation (slices)",
    min_value=0,
    value=saved_donations.get("bread_slices", {}).get("quantity", 120),
    step=1,
)
bread_expiry = st.date_input(
    "Bread expiration date",
    value=saved_donations.get(
        "bread_slices", {}
    ).get("expiry", date(2026, 10, 30)),
)

ham_quantity = st.number_input(
    "Ham donation (slices)",
    min_value=0,
    value=saved_donations.get("ham_slices", {}).get("quantity", 40),
    step=1,
)
ham_expiry = st.date_input(
    "Ham expiration date",
    value=saved_donations.get(
        "ham_slices", {}
    ).get("expiry", date(2026, 10, 30)),
)

cheese_quantity = st.number_input(
    "Cheese donation (slices)",
    min_value=0,
    value=saved_donations.get("cheese_slices", {}).get("quantity", 0),
    step=1,
)
cheese_expiry = st.date_input(
    "Cheese expiration date",
    value=saved_donations.get(
        "cheese_slices", {}
    ).get("expiry", date(2026, 10, 30)),
)

lettuce_quantity = st.number_input(
    "Lettuce donation (bags)",
    min_value=0,
    value=saved_donations.get("lettuce_bags", {}).get("quantity", 0),
    step=1,
)
lettuce_expiry = st.date_input(
    "Lettuce expiration date",
    value=saved_donations.get(
        "lettuce_bags", {}
    ).get("expiry", date(2026, 10, 30)),
)

pickle_quantity = st.number_input(
    "Pickle donation (small jars)",
    min_value=0,
    value=saved_donations.get("pickle_small_jars", {}).get("quantity", 0),
    step=1,
)
pickle_expiry = st.date_input(
    "Pickle expiration date",
    value=saved_donations.get(
        "pickle_small_jars", {}
    ).get("expiry", date(2026, 10, 30)),
)

mustard_quantity = st.number_input(
    "Mustard donation (small bottles)",
    min_value=0,
    value=saved_donations.get(
        "mustard_small_bottles", {}
    ).get("quantity", 0),
    step=1,
)
mustard_expiry = st.date_input(
    "Mustard expiration date",
    value=saved_donations.get(
        "mustard_small_bottles", {}
    ).get("expiry", date(2026, 10, 30)),
)

mayonnaise_quantity = st.number_input(
    "Mayonnaise donation (small bottles)",
    min_value=0,
    value=saved_donations.get(
        "mayonnaise_small_bottles", {}
    ).get("quantity", 0),
    step=1,
)
mayonnaise_expiry = st.date_input(
    "Mayonnaise expiration date",
    value=saved_donations.get(
        "mayonnaise_small_bottles", {}
    ).get("expiry", date(2026, 10, 30)),
)



if st.button("Calculate shopping list"):
    donations = []

    if bread_quantity > 0:
        donations.append({
            "item": "bread_slices",
            "quantity": bread_quantity,
            "expiry": bread_expiry,
        })

    if ham_quantity > 0:
        donations.append({
            "item": "ham_slices",
            "quantity": ham_quantity,
            "expiry": ham_expiry,
        })

    if cheese_quantity > 0:
        donations.append({
            "item": "cheese_slices",
            "quantity": cheese_quantity,
            "expiry": cheese_expiry,
        })

    if lettuce_quantity > 0:
        donations.append({
            "item": "lettuce_bags",
            "quantity": lettuce_quantity,
            "expiry": lettuce_expiry,
        })

    if pickle_quantity > 0:
        donations.append({
            "item": "pickle_small_jars",
            "quantity": pickle_quantity,
            "expiry": pickle_expiry,
        })

    if mustard_quantity > 0:
        donations.append({
            "item": "mustard_small_bottles",
            "quantity": mustard_quantity,
            "expiry": mustard_expiry,
        })

    if mayonnaise_quantity > 0:
        donations.append({
            "item": "mayonnaise_small_bottles",
            "quantity": mayonnaise_quantity,
            "expiry": mayonnaise_expiry,
        })

    replace_donations(donations)
    donations = load_donations()


    results = compute_shopping_list(
        recipe=recipe,
        unit_size=unit_size,
        total_portions=total_portions,
        event_date=event_date,
        donations=donations,
    )

    st.subheader("Shopping list")
    st.dataframe(results)

    kits = make_kits(signups, recipe, unit_size)
    allocated_kits = allocate_donations(kits, donations, event_date)

    st.subheader("Kit assignments")

    kit_rows = []

    for kit in allocated_kits:
        for item, details in kit["ingredients"].items():
            donated_amount = sum(
                lot["quantity"] for lot in details["donated"]
            )
            expiry_dates = ", ".join(
                lot["expiry"].isoformat() for lot in details["donated"]
            )

            kit_rows.append({
                "Volunteer": kit["volunteer"],
                "Portions": kit["portions"],
                "Ingredient": item,
                "Needed": details["needed"],
                "Donated": donated_amount,
                "Expiration dates": expiry_dates,
                "To buy": details["to_buy"],
            })

    if kit_rows:
        st.dataframe(kit_rows, hide_index=True)
    else:
        st.info("There are no signups to assign kits to.")