import pandas as pd
import os

def get_sp500_df():

    # base_path = os.path.dirname(__file__)
    # file_path = os.path.join(base_path, 'data_test','sp500_2022_2024_dataset.csv')
    # path_2_data = path_2_root + 'data_test/'
    # filename = 'sp500_2022_2024_dataset.csv
    csv_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'data_input_streamlit', 'sp500_2022_2024_dataset.csv'))

    df = pd.read_csv(
        csv_path,
        sep=';')
    df_sp500 = df[['Date', 'Price']]
    return df_sp500

data = get_sp500_df()
