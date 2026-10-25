\# Sandwich Angels



Sandwich Angels is a Streamlit web app that helps an existing sandwich volunteer program coordinate event schedules, volunteer signups, donated ingredients, shopping lists, and ingredient kits.



The app is designed to help volunteers understand when to participate and help organizers plan supplies for each event. Each event keeps its own signup and donation information.



\## Features



\### For volunteers

\- View upcoming Friday events and pickup and drop-off details.

\- Create an account and sign up in portions. One portion represents 10 sandwiches.

\- Review current and past volunteer activity.



\### For organizers

\- Create and manage Friday events, participation targets, and event details.

\- Record donated ingredients and expiration dates for each event.

\- Calculate ingredient needs and create a shopping list.

\- Allocate usable donations to volunteer kits, with earlier-expiring items assigned first.

\- Record kit pickup, attendance, and completed sandwich counts.

\- Review volunteer signups and activity history.



\## Technology



\- Python

\- Streamlit

\- SQLite



\## Run locally



1\. Install Python and Git.

2\. Clone this repository:



&#x20;  ```powershell

&#x20;  git clone https://github.com/greglee10/sandwich-angels.git

&#x20;  cd sandwich-angels

&#x20;  ```



3\. Create and activate a virtual environment:



&#x20;  ```powershell

&#x20;  python -m venv .venv

&#x20;  .\\.venv\\Scripts\\Activate.ps1

&#x20;  ```



4\. Install the app dependencies:



&#x20;  ```powershell

&#x20;  pip install -r requirements.txt

&#x20;  ```



5\. Add a local organizer password in `.streamlit/secrets.toml`:



&#x20;  ```toml

&#x20;  \[admin]

&#x20;  password = "replace-with-your-own-password"

&#x20;  ```



&#x20;  Replace the example value with a password of your own. Do not commit `secrets.toml` or share its contents.



6\. Start the app:



&#x20;  ```powershell

&#x20;  streamlit run app.py

&#x20;  ```



\## Important notes



Sandwich Angels is an unofficial planning tool. It does not determine whether food is safe. Volunteers should follow the event organizer’s instructions and applicable food-handling procedures.



The app stores event and signup information in SQLite. Use sample data for demonstrations. Before using the app to manage real volunteer records in a hosted environment, configure a persistent database and review the organization’s privacy and operating requirements.



\## AI assistance



AI tools were used to help troubleshoot errors, review implementation approaches involving Streamlit page state and SQLite event-specific records, and examine edge cases for testing. Suggested changes were checked with tests and sample event data.

