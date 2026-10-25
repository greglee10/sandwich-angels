import streamlit as st
from datetime import date, timedelta

from db import (
    add_signup_for_volunteer,
    get_volunteer_signup,
    initialize_database,
    load_signups,
    load_volunteer_history,
    login_volunteer,
    register_volunteer,
    update_volunteer_signup,
    load_events,
)


st.set_page_config(page_title="Volunteer", page_icon="🥪")
initialize_database()




st.title("Sandwich Angels")
st.caption("Unofficial volunteer tool")
st.warning(
    "The app doesn't check food safety. "
    "Follow the event organizer's instructions."
)

volunteer = st.session_state.get("volunteer")

if volunteer is None:
    st.subheader("Volunteer account")

    create_tab, login_tab = st.tabs(["Create account", "Log in"])

    with create_tab:
        with st.form("create_account_form"):
            new_username = st.text_input("Username")
            display_name = st.text_input("Your name")
            new_pin = st.text_input("Create a 4-digit PIN", type="password")
            create_submitted = st.form_submit_button("Create account")

        if create_submitted:
            success, message = register_volunteer(
                username=new_username,
                display_name=display_name,
                pin=new_pin,
            )

            if success:
                st.success(message)
            else:
                st.error(message)

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            pin = st.text_input("4-digit PIN", type="password", key="login_pin")
            login_submitted = st.form_submit_button("Log in")

        if login_submitted:
            logged_in_volunteer = login_volunteer(username, pin)

            if logged_in_volunteer is None:
                st.error("Username or PIN was not recognized.")
            else:
                st.session_state["volunteer"] = logged_in_volunteer
                st.rerun()

    st.stop()


st.sidebar.write(f"Logged in as {volunteer['display_name']}")

if st.sidebar.button("Log out"):
    del st.session_state["volunteer"]
    st.rerun()

st.subheader(f"Welcome, {volunteer['display_name']}")


open_events = load_events()

if not open_events:
    st.info("There are no open events yet. Please check again later.")
    st.stop()

event_dates = [event["event_date"] for event in open_events]

event_date = st.selectbox(
    "Choose a Friday event",
    options=event_dates,
    format_func=lambda value: value.strftime("%A, %B %d, %Y"),
)

selected_event = next(
    event for event in open_events
    if event["event_date"] == event_date
)

target_portions = selected_event["target_portions"]
pickup_date = event_date - timedelta(days=1)

st.write(f"Thursday pickup: {pickup_date.strftime('%A, %B %d, %Y')}")
st.write(selected_event["pickup_details"])
st.write(f"Friday drop-off: {event_date.strftime('%A, %B %d, %Y')}")
st.write(selected_event["dropoff_details"])


signups = load_signups(event_date)
signed_portions = sum(signup["portions"] for signup in signups)
remaining_portions = target_portions - signed_portions

st.write(f"Signed up: {signed_portions} / {target_portions} portions")
st.write(f"Remaining: {remaining_portions} portions")

my_signup = get_volunteer_signup(
    volunteer["volunteer_id"],
    event_date,
)

if my_signup is None:
    st.subheader("Sign up for this event")

    if remaining_portions > 0:
        with st.form("event_signup_form"):
            portions = st.number_input(
                "Portions (1 portion = 10 sandwiches)",
                min_value=1,
                max_value=remaining_portions,
                value=1,
                step=1,
            )
            signup_submitted = st.form_submit_button("Sign up")

        if signup_submitted:
            success, message = add_signup_for_volunteer(
                volunteer_id=volunteer["volunteer_id"],
                portions=int(portions),
                target_portions=target_portions,
                event_date=event_date,
            )

            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    else:
        st.info("The signup target has been reached.")

else:
    st.subheader("My signup")
    st.write(f"Your current signup: {my_signup['portions']} portion(s)")
    st.write("1 portion = 10 sandwiches.")

    with st.form("edit_event_signup_form"):
        new_portions = st.number_input(
            "Change your portion amount",
            min_value=1,
            max_value=target_portions,
            value=my_signup["portions"],
            step=1,
        )
        update_submitted = st.form_submit_button("Update my signup")

    if update_submitted:
        success, message = update_volunteer_signup(
            volunteer_id=volunteer["volunteer_id"],
            event_date=event_date,
            new_portions=int(new_portions),
            target_portions=target_portions,
        )

        if success:
            st.success(message)
            st.rerun()
        else:
            st.error(message)


st.divider()
st.subheader("My past volunteer activities")

history = load_volunteer_history(volunteer["volunteer_id"])
past_history = [
    record
    for record in history
    if record["event_date"] <= date.today()
]

if past_history:
    history_rows = [
        {
            "Event date": record["event_date"].isoformat(),
            "Portions": record["portions"],
            "Sandwiches": record["portions"] * 10,
            "Attendance": (
                "Confirmed"
                if record["attended"]
                else "Awaiting organizer confirmation"
            ),
        }
        for record in past_history
    ]

    st.dataframe(history_rows, hide_index=True)
else:
    st.info("No past volunteer activities yet.")