import streamlit as st
import pandas as pd
import zipfile
import tempfile
import os
import hashlib

from backend.html_to_csv import parse_google_pay_html_to_csv
from backend.analysis import analyze_google_pay, analyze_bank
from backend.gemini_helper import generate_gemini_summary

st.set_page_config(page_title="Finance Tracker", layout="wide")
st.title("💸 Personal Finance Tracker")

# ------------------------- Sidebar Guide --------------------------
st.sidebar.header("📁 How to Get Your Google Pay ZIP")
st.sidebar.markdown("""
1. Go to [Google Takeout](https://takeout.google.com/)
2. Deselect all and scroll down to **Google Pay**
3. Select **HTML format**, then click **Next Step**
4. Choose "Export once" and click **Create Export**
5. Once ready, download the ZIP
6. Upload the ZIP file here
""")

# ------------------------- Helpers --------------------------
def get_file_md5(file_bytes):
    md5 = hashlib.md5()
    md5.update(file_bytes)
    return md5.hexdigest()

@st.cache_data(show_spinner="🔄 Processing uploaded ZIP...")
def extract_gpay_html_from_zip(zip_bytes, file_hash):
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "takeout.zip")
        with open(zip_path, "wb") as f:
            f.write(zip_bytes)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)

        gpay_html_path = None
        for root, _, files in os.walk(tmpdir):
            for file in files:
                if file.endswith(".html") and "My Activity" in root and "Google Pay" in root:
                    gpay_html_path = os.path.join(root, file)
                    break

        if not gpay_html_path:
            return None

        temp_csv_path = os.path.join(tmpdir, "transactions.csv")
        parse_google_pay_html_to_csv(gpay_html_path, temp_csv_path)
        df = pd.read_csv(temp_csv_path)
        return df

@st.cache_data(show_spinner="🔄 Parsing HTML...")
def parse_uploaded_html(file_bytes, file_hash):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
        tmp_file.write(file_bytes)
        temp_html_path = tmp_file.name
    temp_csv_path = temp_html_path.replace(".html", ".csv")
    parse_google_pay_html_to_csv(temp_html_path, temp_csv_path)
    df = pd.read_csv(temp_csv_path)
    return df

@st.cache_data(show_spinner=False)
def get_week_df(df, selected_date):
    week_start = selected_date - pd.to_timedelta(selected_date.weekday(), unit='d')
    week_end = week_start + pd.Timedelta(days=6)
    week_df = df[(df['Raw Timestamp'].dt.date >= week_start) & (df['Raw Timestamp'].dt.date <= week_end)]
    return week_df, week_start, week_end

@st.cache_data(show_spinner=False)
def get_month_df(df, month):
    return df[df['Month'] == month]

@st.cache_data(show_spinner="🧠 Summarizing with Gemini...")
def cached_gemini_summary(key: str, filtered_df: pd.DataFrame):
    return generate_gemini_summary(filtered_df)

# ----------------------- File Upload ------------------------
uploaded_file = st.file_uploader("📄 Upload ZIP / HTML / CSV", type=['zip', 'csv', 'html', 'txt'])

if uploaded_file:
    file_bytes = uploaded_file.read()
    file_hash = get_file_md5(file_bytes)

    if uploaded_file.name.endswith(".zip"):
        df = extract_gpay_html_from_zip(file_bytes, file_hash)
        if df is None:
            st.error("❌ Google Pay 'My Activity.html' not found in ZIP.")
            st.stop()
        mode = 'Google Pay'

    elif uploaded_file.name.endswith('.html') or uploaded_file.name.endswith('.txt'):
        df = parse_uploaded_html(file_bytes, file_hash)
        mode = 'Google Pay'

    elif uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
        if 'Time' in df.columns and 'Amount' in df.columns:
            mode = 'Google Pay'
        elif 'Balance' in df.columns and 'Debit' in df.columns:
            mode = 'Bank'
        else:
            st.error("Unsupported CSV format.")
            st.stop()
    else:
        st.error("Unsupported file type.")
        st.stop()

    # -------------------- Preprocessing ----------------------
    st.sidebar.success(f"🧠 Auto-detected Source: {mode}")

    if 'Type' in df.columns:
        df['Type'] = df['Type'].astype(str).str.strip().str.capitalize()

    if 'Time' in df.columns and 'Date' in df.columns:
        df['Raw Timestamp'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'], errors='coerce')
        df['Hour'] = df['Raw Timestamp'].dt.hour.fillna(0).astype(int)
        df['Weekday'] = df['Raw Timestamp'].dt.day_name()
        df['Week'] = df['Raw Timestamp'].dt.to_period('W').apply(lambda r: r.start_time.date())
        df['Month'] = df['Raw Timestamp'].dt.to_period('M').apply(lambda r: r.start_time.strftime('%Y-%m'))
        df['AM/PM'] = df['Raw Timestamp'].dt.strftime('%p').fillna('')
    else:
        st.error("Required columns 'Date' and 'Time' not found.")
        st.stop()

    # ------------------------ TABS --------------------------
    tab1, tab2, tab3, tab4 = st.tabs([
        "🗕️ Daily View",
        "🏜️ Weekly View",
        "🗓️ Monthly View",
        "📄 Transaction Table"
    ])

    today = pd.Timestamp.today().date()

    # -------- Daily --------
    with tab1:
        st.subheader("🗕️ Daily Transactions")
        selected_day = st.date_input("Choose a day", value=today, max_value=today, key='daily_date')
        day_df = df[df['Raw Timestamp'].dt.date == selected_day]

        st.dataframe(day_df)
        st.metric("💸 Total Sent", f"₹ {abs(day_df[day_df['Type']=='Sent']['Amount'].sum()):,.2f}")
        st.metric("💰 Total Received", f"₹ {day_df[day_df['Type']=='Received']['Amount'].sum():,.2f}")

        spending_day = day_df[day_df['Type'] == 'Sent']
        avg_spent_day = spending_day['Amount'].sum() / len(spending_day) if len(spending_day) > 0 else 0
        st.metric("📊 Avg Spending per Sent Txn", f"₹ {avg_spent_day:.2f}")

        if st.checkbox("Show Spending Only", key='spending_only_daily'):
            st.dataframe(spending_day)

    # -------- Weekly --------
    with tab2:
        st.subheader("🏜️ Weekly Transactions")
        selected_week_date = st.date_input("Choose a date", value=today, max_value=today, key='weekly_date')
        week_df, week_start, week_end = get_week_df(df, selected_week_date)

        st.markdown(f"#### Week Range: {week_start} → {week_end}")
        st.dataframe(week_df)
        st.metric("💸 Weekly Sent", f"₹ {abs(week_df[week_df['Type']=='Sent']['Amount'].sum()):,.2f}")
        st.metric("💰 Weekly Received", f"₹ {week_df[week_df['Type']=='Received']['Amount'].sum():,.2f}")

        spending_week = week_df[week_df['Type'] == 'Sent']
        num_days_week = spending_week['Raw Timestamp'].dt.date.nunique()
        avg_daily_spent_week = spending_week['Amount'].sum() / num_days_week if num_days_week > 0 else 0
        st.metric("📊 Avg Daily Spending (Sent)", f"₹ {avg_daily_spent_week:.2f}")

        if st.checkbox("Show Spending Only", key='spending_only_weekly'):
            st.dataframe(spending_week)

        if not week_df.empty and st.button("🧠 Generate Weekly AI Summary"):
            summary_key = f"week-{week_start}-{file_hash}"
            st.markdown(cached_gemini_summary(summary_key, week_df))

    # -------- Monthly --------
    with tab3:
        st.subheader("🗓️ Monthly Transactions")
        all_months = sorted(df['Month'].dropna().unique(), reverse=True)
        selected_month = st.selectbox("Choose a month", all_months, index=0)
        month_df = get_month_df(df, selected_month)

        st.dataframe(month_df)
        st.metric("💸 Monthly Sent", f"₹ {abs(month_df[month_df['Type']=='Sent']['Amount'].sum()):,.2f}")
        st.metric("💰 Monthly Received", f"₹ {month_df[month_df['Type']=='Received']['Amount'].sum():,.2f}")

        spending_month = month_df[month_df['Type'] == 'Sent']
        num_days_month = spending_month['Raw Timestamp'].dt.date.nunique()
        avg_daily_spent_month = spending_month['Amount'].sum() / num_days_month if num_days_month > 0 else 0
        st.metric("📊 Avg Daily Spending (Sent)", f"₹ {avg_daily_spent_month:.2f}")

        if st.checkbox("Show Spending Only", key='spending_only_monthly'):
            st.dataframe(spending_month)

        if not month_df.empty and st.button("🧠 Generate Monthly AI Summary"):
            summary_key = f"month-{selected_month}-{file_hash}"
            st.markdown(cached_gemini_summary(summary_key, month_df))

    # -------- All Transactions --------
    with tab4:
        st.subheader("📄 Full Transaction Table")

        # Add search and amount filter
        col1, col2 = st.columns(2)
        with col1:
            search_text = st.text_input("🔍 Search Description")
        with col2:
            amt_range = st.slider("💵 Amount Range", min_value=int(df['Amount'].min()), max_value=int(df['Amount'].max()), value=(int(df['Amount'].min()), int(df['Amount'].max())))

        filtered_df = df.copy()
        if search_text:
            filtered_df = filtered_df[filtered_df['Description'].str.contains(search_text, case=False, na=False)]
        filtered_df = filtered_df[(filtered_df['Amount'] >= amt_range[0]) & (filtered_df['Amount'] <= amt_range[1])]

        st.dataframe(filtered_df)

else:
    st.info("Please upload a transaction file (ZIP, HTML, or CSV)")