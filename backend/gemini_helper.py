import streamlit as st
import google.generativeai as genai
import pandas as pd

# ✅ Secure API Key from .streamlit/secrets.toml
genai.configure(api_key=st.secrets["api_keys"]["gemini_key"])

def generate_gemini_summary(df):
    # Prepare main content
    prompt_data = df[['Date', 'Description', 'Amount', 'Type']].to_string(index=False)

    # 🕒 Extract top 2 spending hours
    df['Hour'] = pd.to_datetime(df['Time'], errors='coerce').dt.hour
    hour_counts = df[df['Type'] == 'Sent']['Hour'].value_counts().nlargest(2)
    top_hours = ', '.join([f"{int(h)}:00" for h in hour_counts.index if pd.notnull(h)])

    # 🧠 Build prompt
    prompt = f"""
    You are a smart finance assistant.
    Analyze the following transactions and summarize:

    - Total money sent and received
    - Largest transaction
    - Most frequent sender/recipient
    - Spending trends

    Also mention:
    - Which hours the user spends money most often. Based on data: {top_hours}

    Transactions:
    {prompt_data}
    """

    model = genai.GenerativeModel("models/gemini-2.0-flash")
    chat = model.start_chat()
    response = chat.send_message(prompt)

    return response.text
