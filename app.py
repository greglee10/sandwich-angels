import streamlit as st


st.set_page_config(page_title="Sandwich Angels", page_icon="🥪")

st.title("Sandwich Angels")
st.caption("Unofficial volunteer tool")
st.warning(
    "The app doesn't check food safety. "
    "Follow the event organizer's instructions."
)
st.write("Choose a page from the sidebar.")
st.write("Volunteer is for sign-ups. Organizer is password protected.")