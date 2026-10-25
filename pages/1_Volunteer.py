import streamlit as st
from datetime import date

from db import (
    add_signup_for_volunteer,
    get_volunteer_signup,
    initialize_database,
    load_signups,
    login_volunteer,
    register_volunteer,
    update_volunteer_signup,
)


st.set_page_config(page_title="Volunteer", page_icon="🥪")
initialize_database()

event_date = date(2026, 10, 30)
target_portions = 9

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