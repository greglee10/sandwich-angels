from datetime import date

import streamlit as st

from db import (
    add_signup,
    initialize_database,
    load_donations,
    load_signups,
    replace_donations,
    load_completed_count,
    save_completed_count,
    load_received_signup_ids,
    set_kit_received,
    load_admin_signup_history,
    set_signup_attendance,
)

from core.planner import compute_shopping_list

from core.kit_splitter import make_kits, allocate_donations

if not st.session_state.get("admin_authenticated", False):
    st.title("Organizer login")
    password = st.text_input("Organizer password", type="password")

    if st.button("Log in"):
        if password == st.secrets["admin"]["password"]:
            st.session_state["admin_authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")

    st.stop()

if st.sidebar.button("Log out"):
    st.session_state["admin_authenticated"] = False
    st.rerun()

def save_receipt(signup_id, state_key):
    set_kit_received(
        signup_id,
        st.session_state[state_key],
    )

initialize_database()

target_portions = 9
signups = load_signups()
signed_portions = sum(signup["portions"] for signup in signups)
remaining_portions = target_portions - signed_portions



saved_donations = {
    donation["item"]: donation
    for donation in load_donations()
}

st.title("Sandwich Angels")
st.caption("Unofficial volunteer tool")
st.warning("The app doesn't check food safety. Follow the event organizer's instructions.")
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

receipt_donations = load_donations()
receipt_kits = make_kits(signups, recipe, unit_size)
receipt_allocations = allocate_donations(
    receipt_kits,
    receipt_donations,
    event_date,
)
received_signup_ids = load_received_signup_ids()

if receipt_allocations:
    st.subheader("Kit pickup")

    for kit in receipt_allocations:
        state_key = f"kit_received_{kit['signup_id']}"

        st.checkbox(
            f"{kit['volunteer']} received kit",
            value=kit["signup_id"] in received_signup_ids,
            key=state_key,
            on_change=save_receipt,
            args=(kit["signup_id"], state_key),
        )

st.subheader("Event completion")

planned_sandwiches = signed_portions * unit_size
saved_completed_count = load_completed_count(event_date)

st.write(f"Planned sandwiches: {planned_sandwiches}")

completed_count = st.number_input(
    "Sandwiches completed",
    min_value=0,
    value=saved_completed_count,
    step=1,
    key=f"completed_count_{event_date.isoformat()}",
)

st.write(f"Completed: {int(completed_count)} / {planned_sandwiches}")

if completed_count < planned_sandwiches:
    shortfall = planned_sandwiches - int(completed_count)
    st.warning(f"{shortfall} more sandwiches are needed to reach the target.")
elif completed_count == planned_sandwiches:
    st.success("The planned sandwich count has been reached.")
else:
    st.warning(
        "The completed count is higher than the planned count. Please verify it."
    )

if st.button("Save completed count"):
    save_completed_count(event_date, int(completed_count))
    st.success("Completed count saved.")


st.divider()
st.subheader("Volunteer roster and activity history")

history = load_admin_signup_history()

if not history:
    st.info("No volunteer signups yet.")
else:
    st.write("Mark attendance after each activity, then save your changes.")

    with st.form("admin_attendance_form"):
        header = st.columns([2, 1.5, 1, 1, 1.5])
        header[0].write("Volunteer")
        header[1].write("Username")
        header[2].write("Event date")
        header[3].write("Portions")
        header[4].write("Attendance")

        for record in history:
            columns = st.columns([2, 1.5, 1, 1, 1.5])

            columns[0].write(record["display_name"])
            columns[1].write(record["username"] or "Earlier signup")
            columns[2].write(record["event_date"].isoformat())
            columns[3].write(record["portions"])

            columns[4].checkbox(
                "Attended",
                value=record["attended"],
                key=f"attendance_{record['signup_id']}",
            )

        save_attendance = st.form_submit_button("Save attendance")

    if save_attendance:
        for record in history:
            set_signup_attendance(
                record["signup_id"],
                st.session_state[f"attendance_{record['signup_id']}"],
            )

        st.success("Attendance records saved.")
        st.rerun()