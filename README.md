# 💸 Google Pay Finance Tracker

This is a smart, interactive finance tracking app built using **Streamlit** and **Gemini AI**. It helps you **analyze your Google Pay transactions** by simply uploading a `.ZIP`, `.CSV`, or `.HTML` file exported from [Google Takeout](https://takeout.google.com/).

🔗 **Live App:** [Click to Use](https://app-pay-finance-tracker-cmgwzdrxpnpb3dicmdp5mg.streamlit.app/)

---

## ✨ Features

- 🔐 **Secure ZIP upload** — just drop your Google Takeout `.zip`, the app will do the rest.
- 📊 **Daily, Weekly, and Monthly Views** with date filters
- 🔍 **Transaction Table Filtering** by:
  - Description (search)
  - Amount range (slider)
- 🧠 **Gemini AI-powered Insights** per week/month
- 🧮 **Auto MD5 Hashing** of uploaded files for smart caching
- 📁 Parses and cleans raw Google Pay HTML into CSV format

---

## 📁 How to Use

### 1. Export Google Pay Data
- Go to [Google Takeout](https://takeout.google.com/)
- Deselect all and scroll down to **Google Pay**
- Choose **HTML format**
- Click **Next Step** → Select **Export Once**
- Download the `.ZIP` file when it's ready

### 2. Upload to the App
- Drag & drop the `.ZIP` file into the app
- The app auto-detects the data and shows insights

---

## 🛠 Tech Stack

- **Streamlit** – interactive frontend
- **Python + Pandas** – data parsing and analysis
- **Gemini (Google Generative AI)** – summary generation
- **BeautifulSoup** – HTML parsing
- **Matplotlib / Seaborn** – (optional for future enhancements)

---

## 🔐 Secrets Handling

This project uses `.streamlit/secrets.toml` to securely load your Gemini API key.

```toml
[api_keys]
gemini_key = "YOUR_API_KEY"
