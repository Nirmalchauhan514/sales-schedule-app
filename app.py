import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Sales Schedule", layout="wide")

# --- Google Sheets auth using Streamlit secrets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

try:
    credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(credentials)
except Exception as e:
    st.error("Failed to authorize with Google Sheets API. Check your Streamlit secrets and credentials.")
    st.write(e)
    st.stop()

# --- Open sheet ---
SHEET_NAME = "Sales_Schedule"
try:
    sheet = client.open(SHEET_NAME).sheet1
except Exception as e:
    st.error(f"Cannot open Google Sheet named '{SHEET_NAME}'. Make sure it exists and the service account has Editor access.")
    st.write(e)
    st.stop()

st.title("📅 Sales Daily Schedule")

# --- Form to submit schedule ---
st.subheader("Add Schedule")
name = st.text_input("Your Name")
schedule_date = st.date_input("Select Date", value=datetime.now().date())  # Date picker

if "rows" not in st.session_state:
    st.session_state.rows = [{"time": datetime.now().time(), "location": ""}]

# Display dynamic rows
for i, row in enumerate(st.session_state.rows):
    col1, col2 = st.columns([1, 3])
    with col1:
        row["time"] = st.time_input(f"Time {i+1}", value=row["time"], key=f"time_{i}")
    with col2:
        row["location"] = st.text_input(f"Location {i+1}", value=row["location"], key=f"loc_{i}")

# Add/Remove rows buttons
col_add, col_remove = st.columns(2)
with col_add:
    if st.button("➕ Add Another Location"):
        st.session_state.rows.append({"time": datetime.now().time(), "location": ""})
with col_remove:
    if st.button("➖ Remove Last Location") and len(st.session_state.rows) > 1:
        st.session_state.rows.pop()

# Submit button
if st.button("✅ Submit Schedule"):
    rows_to_add = []
    for r in st.session_state.rows:
        if not r["location"]:
            st.error("Please fill all location fields before submitting.")
            st.stop()
        rows_to_add.append([
            schedule_date.strftime("%Y-%m-%d"),
            name,
            r["location"],
            str(r["time"])
        ])

    try:
        for row in rows_to_add:
            sheet.append_row(row)
        st.success("✅ Schedule submitted successfully!")
    except Exception as e:
        st.error("Failed to write to Google Sheet. Check sharing and network.")
        st.write(e)

# --- Manager view (hidden by password) ---
st.markdown("---")
st.subheader("📊 Manager View (Restricted)")

manager_password = st.text_input("Enter Manager Password", type="password")
if manager_password == "admin123":  # Change this password as needed
    try:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
    except Exception as e:
        st.error("Failed to read data from Google Sheet.")
        st.write(e)
        st.stop()

    if df.empty:
        st.info("No schedule entries yet.")
    else:
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download CSV", csv, "sales_schedule.csv", "text/csv")
elif manager_password != "":
    st.error("Incorrect password.")
