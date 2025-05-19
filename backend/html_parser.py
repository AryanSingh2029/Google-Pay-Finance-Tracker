import re
import pandas as pd
from datetime import datetime

def parse_gpay_text_file(text):
    entries = text.split("Google Pay")
    data = []

    for entry in entries:
        if not entry.strip():
            continue

        # Default values
        amount = None
        description = "N/A"
        txn_type = None

        # Case 1: Paid to someone
        match_paid = re.search(r'Paid ₹([\d,.]+) to (.+?) using', entry)
        if match_paid:
            amount = -float(match_paid.group(1).replace(",", ""))
            description = f"Paid to {match_paid.group(2).strip()}"
            txn_type = "Sent"

        # Case 2: Sent (assume we received money)
        match_sent = re.search(r'Sent ₹([\d,.]+) using', entry)
        if match_sent:
            amount = float(match_sent.group(1).replace(",", ""))
            description = "Received money"
            txn_type = "Received"

        # Case 3: Extract Date & Time
        date_match = re.search(r'([A-Za-z]+ \d{1,2}, \d{4}, \d{1,2}:\d{2}:\d{2})', entry)
        if not date_match:
            continue
        date_str = date_match.group(1)
        dt = datetime.strptime(date_str, '%b %d, %Y, %I:%M:%S')

        data.append({
            "Date": dt.strftime('%Y-%m-%d'),       # Clean date
            "Time": dt.strftime('%H:%M'),           # Clean time
            "Description": description,
            "Amount": amount,
            "Type": txn_type
        })

    return pd.DataFrame(data)
