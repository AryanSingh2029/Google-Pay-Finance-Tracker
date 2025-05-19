import pandas as pd

def clean_google_pay(df):
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Hour'] = pd.to_datetime(df['Time'], errors='coerce').dt.hour
    df['Weekday'] = df['Date'].dt.day_name()
    df['Week'] = df['Date'].dt.to_period('W').apply(lambda r: r.start_time.strftime('%Y-%m-%d'))
    df['Month'] = df['Date'].dt.to_period('M').astype(str)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)

    # ✅ Add this to clean 'Type'
    if 'Type' in df.columns:
        df['Type'] = df['Type'].astype(str).str.strip().str.capitalize()

    return df


def clean_bank(df):
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Weekday'] = df['Date'].dt.day_name()
    df['Debit'] = pd.to_numeric(df['Debit'], errors='coerce').fillna(0)
    df['Credit'] = pd.to_numeric(df['Credit'], errors='coerce').fillna(0)
    df['Balance'] = pd.to_numeric(df['Balance'], errors='coerce').fillna(method='ffill')
    return df

def analyze_google_pay(df):
    df = clean_google_pay(df)
    daily = df.groupby('Date')['Amount'].sum().reset_index()
    time_day = df.groupby('Hour')['Amount'].sum().reset_index()
    weekday = df.groupby('Weekday')['Amount'].sum().reset_index()
    return 'Google Pay', df, daily, time_day, weekday

def analyze_bank(df):
    df = clean_bank(df)
    daily = df.groupby('Date')['Debit'].sum().reset_index()
    weekday = df.groupby('Weekday')['Debit'].sum().reset_index()
    return 'Bank', df, daily, weekday
def generate_summary(df):
    if 'Type' not in df.columns or 'Amount' not in df.columns:
        return {
            'Date': pd.DataFrame(columns=['Date', 'Sent', 'Received']),
            'Week': pd.DataFrame(columns=['Week', 'Sent', 'Received']),
            'Month': pd.DataFrame(columns=['Month', 'Sent', 'Received']),
        }

    df['Date'] = pd.to_datetime(df['Date'])
    df['Week'] = df['Date'].dt.to_period('W').apply(lambda r: r.start_time.strftime('%Y-%m-%d'))
    df['Month'] = df['Date'].dt.to_period('M').astype(str)

    summary = {}

    for level in ['Date', 'Week', 'Month']:
        grouped = df.groupby([level, 'Type'])['Amount'].sum().unstack(fill_value=0)
        grouped.columns.name = None
        grouped.reset_index(inplace=True)
        summary[level] = grouped

    return summary
