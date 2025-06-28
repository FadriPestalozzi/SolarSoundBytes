import pandas as pd
import os


def create_df_of_twitter_result():
    # base_path = os.path.dirname(__file__)
    # file_path = os.path.join(base_path, 'data_test', 'twitter_sentiment_analysis_UTF8.csv')
    # file_path = '../data/csv/twitter_sentiment_analysis_UTF8.csv'
    csv_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'data_input_streamlit', 'TwitterDays_with_sentiment_0613.csv'))

    data = pd.read_csv(csv_path,  encoding='utf-8')

    df = data[['Date', 'distilbert_pos_score', 'distilbert_neg_score']]
    df = df.rename(columns={'distilbert_pos_score': 'pos_score',
                            'Date': 'date',
                            'distilbert_neg_score': 'neg_score'})
    return df

def create_df_of_twitter_result_events():
    # base_path = os.path.dirname(__file__)
    # file_path = os.path.join(base_path, 'data_test', 'twitter_sentiment_analysis_UTF8.csv')
    # file_path = '../data/csv/twitter_sentiment_analysis_UTF8.csv'
    csv_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'data_input_streamlit', 'TwitterEvents_with_sentiment_timestamp.xlsx'))

    data = pd.read_excel(csv_path)

    df = data[['Clean_Date', 'distilbert_pos_score', 'distilbert_neg_score']]
    df = df.rename(columns={'distilbert_pos_score': 'pos_score',
                            'Clean_Date': 'date',
                            'distilbert_neg_score': 'neg_score'})
    return df

test = create_df_of_twitter_result()
print(test.head())
