import pandas as pd
from data_sp500 import get_sp500_df



def preprocess_sp500_df():
    df_sp500 = get_sp500_df()

    # Prepare S&P 500
    df_sp500['Date'] = pd.to_datetime(df_sp500['Date'], format='%m/%d/%Y', errors='coerce')
    df_sp500['Price'] = df_sp500['Price'].str.replace(',', '')
    df_sp500['Price'] = pd.to_numeric(df_sp500['Price'], errors='coerce')
    df_sp500['month'] = df_sp500['Date'].dt.to_period('M')
    monthly_sp500 = df_sp500.groupby('month')['Price'].mean().reset_index()
    monthly_sp500['month'] = monthly_sp500['month'].dt.to_timestamp()

    return monthly_sp500
