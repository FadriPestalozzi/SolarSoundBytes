import pandas as pd
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

api_key = os.getenv("API_KEY")


def create_text_from_sent_analy_df(data_twitter, data_news, data_sp500, data_energy, selected_metrics=None, relevant_events=None):
    """
    Create text analysis with filtered data based on what's actually displayed in the dashboard.
    If no filtering parameters are provided, includes all available data (backwards compatible).
    """
    
    # Build the data section of the prompt dynamically
    data_sections = []
    
    # Always include sentiment data
    data_sections.append(f"Twitter sentiment data:\n{data_twitter}")
    data_sections.append(f"News sentiment data:\n{data_news}")
    
    # Handle metrics inclusion - if no selected_metrics provided, include all available data
    if selected_metrics is None:
        # No filtering - include all available data
        if not data_sp500.empty:
            data_sections.append(f"S&P 500 data:\n{data_sp500}")
        if not data_energy.empty:
            data_sections.append(f"Renewable energy capacity data:\n{data_energy}")
    else:
        # Apply filtering based on selected metrics
        if 'S&P 500' in selected_metrics and not data_sp500.empty:
            data_sections.append(f"S&P 500 data:\n{data_sp500}")
        if 'Installed Capacity Renewables' in selected_metrics and not data_energy.empty:
            data_sections.append(f"Renewable energy capacity data:\n{data_energy}")
    
    # Build the events section
    events_text = ""
    if relevant_events is None:
        # No filtering - include all major events for context
        events_text = """- Consider the following major events for context:
  - 2022-02-24: Russian invasion of Ukraine & global energy crisis
  - 2022-05-18: EU adopts REPowerEU plan (cut Russian fuel, boost renewables)
  - 2022-08-16: US Inflation Reduction Act
  - 2023-05-30: Solar > Oil investment tipping point (IEA Report)
  - 2023-12-12: COP28 climate summit - pledge to triple renewables by 2030
  - 2022-12-31: Global solar capacity surpasses 1 TW (year-end milestone)"""
    elif relevant_events:
        events_text = "- Events that occurred during this period:\n" + "\n".join([f"  - {event}" for event in relevant_events])
    else:
        events_text = "- No major events occurred during the selected time period."
    
    # Build the metrics context
    metrics_context = ""
    if selected_metrics:
        metrics_context = f"Focus your analysis on the following metrics that were displayed: {', '.join(selected_metrics)}. "
    
    prompt = f"""
    Here you have datasets regarding sentiment analysis of tweets and news articles for renewable energy topics:
    
    {chr(10).join(data_sections)}
    
    Please summarize the development of public opinion during the selected time period.
    {metrics_context}
    - Explain whether the perception in social media and in news media was different and why
    - Consider the following context:
    {events_text}
    
    Write a structured analysis of about 100-150 words focusing on the data and events within the timeframe.
    """

    client = OpenAI(api_key = api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a data-analytical journalist specializing in renewable energy sentiment analysis."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=1000
    )

    return response.choices[0].message.content

# Example usage:
# output = create_text_from_sent_analy_df(result_twitter, result_news, result_sp500, result_energy)
# print(output)
