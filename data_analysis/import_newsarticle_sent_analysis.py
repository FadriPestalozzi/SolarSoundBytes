import pandas as pd
import os


def create_df_of_newsarticle_result():
    # base_path = os.path.dirname(__file__)
    # file_path = os.path.join(base_path, 'data_test', 'cleantech_predictions_with_confidence _UTF8.xlsx')
    csv_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'data_input_streamlit', 'combined_articles_with_sentiment.csv'))

    data = pd.read_csv(csv_path)

    df = data[['Clean_Date', 'distilbert_pos_score', 'distilbert_neg_score']]
    df = df.rename(columns={'distilbert_pos_score': 'pos_score',
                            'Clean_Date': 'date',
                            'distilbert_neg_score': 'neg_score'})
    return df


test = create_df_of_newsarticle_result()
print(test.head())
