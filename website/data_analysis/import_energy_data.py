import pandas as pd
import os


def get_energy_df():

    csv_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'data_input_streamlit', 'monthly_capacity_wind_solar_public_release_file.csv'))

    df = pd.read_csv(
        csv_path)

    df['Month'] = df['Month'].astype(int)
    df['Year'] = df['Year'].astype(int)

    # Create a new 'Date' column
    df['Date'] = pd.to_datetime(df['Year'].astype(str) + '-' + df['Month'].astype(str) + '-01')
    df = df.drop(columns=['Month', 'Year'])

    df = df[df['Date'].dt.year.isin([2022, 2023, 2024])]
    df_result = df.groupby('Date')['Installed Capacity'].sum().reset_index()

    return df_result

# data = get_energy_df()
# print(data.head())



## IRENA + prediction
# def get_energy_df():

#     csv_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'data', 'csv', 'IRENA_plus_prediction2024.csv'))

#     df = pd.read_csv(
#         csv_path)

#     data = df[['Unnamed: 0', 'share', 'renewables']]
#     data = data.rename(columns={'Unnamed: 0': 'year'})

#     return data

# data = get_energy_df()
# print(data.head())
