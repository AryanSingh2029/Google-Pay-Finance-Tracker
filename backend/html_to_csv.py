from bs4 import BeautifulSoup
import re
from dateutil.parser import parse
import pandas as pd

def parse_google_pay_html_to_csv(html_file_path, csv_file_path):
    with open(html_file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    transactions = []

    transaction_divs = soup.find_all('div', class_='mdl-grid')

    for div in transaction_divs:
        # Check the specific 'details' div for 'Completed'
        details_div = div.find('div', class_='content-cell mdl-cell mdl-cell--12-col mdl-typography--caption')
        if not details_div or 'Completed' not in details_div.get_text():
            continue  # Skip incomplete transactions

        content_cells = div.find_all('div', class_='content-cell')

        if not content_cells or len(content_cells) < 2:
            continue

        desc_time_div = content_cells[0]
        text = desc_time_div.get_text(separator='\n').strip()

        datetime_line = None
        description_line = None

        lines = text.split('\n')
        for line in lines:
            if 'AM' in line or 'PM' in line:
                datetime_line = line.strip()
            else:
                if description_line:
                    description_line += " " + line.strip()
                else:
                    description_line = line.strip()

        if not datetime_line:
            datetime_line = ''

        description = description_line if description_line else ''
        raw_timestamp = datetime_line
        timestamp_clean = raw_timestamp.split(' GMT')[0]

        try:
            dt = parse(timestamp_clean)
            date_str = dt.strftime('%Y-%m-%d')
            time_str = dt.strftime('%I:%M:%S %p')
        except Exception:
            date_str = ''
            time_str = ''

        amount_match = re.search(r'[-+]?\d*\.?\d+', description.replace(',', ''))
        amount = amount_match.group() if amount_match else '0'

        # Updated Type detection logic
        desc_lower = description.lower()
        if 'paid' in desc_lower:
            tx_type = 'Sent'
        elif 'sent' in desc_lower:
            tx_type = 'Received'
        else:
            tx_type = 'Received'  # fallback default

        transactions.append({
            'Date': date_str,
            'Time': time_str,
            'Description': description,
            'Amount': amount,
            'Type': tx_type
        })

    # Remove duplicates based on key columns
    df_tx = pd.DataFrame(transactions)
    df_tx = df_tx.drop_duplicates(subset=['Date', 'Time', 'Amount', 'Description'])

    df_tx.to_csv(csv_file_path, index=False)

    print(f"Converted HTML transactions to CSV at {csv_file_path}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print("Usage: python html_to_csv.py input.html output.csv")
    else:
        parse_google_pay_html_to_csv(sys.argv[1], sys.argv[2])
