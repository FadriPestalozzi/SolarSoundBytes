# --- Imports from sentiment_viz.py and dashboard.py merged ---
import streamlit as st
import plotly.graph_objs as go
import plotly.graph_objects as go2
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data_analysis.import_twitter_sent_analysis import create_df_of_twitter_result, create_df_of_twitter_result_events
from data_analysis.import_newsarticle_sent_analysis import create_df_of_newsarticle_result
from data_analysis.process_sp500_df import preprocess_sp500_df
from data_analysis.import_energy_data import get_energy_df
from data_analysis.text_creation.create_text import create_text_from_sent_analy_df
from gtts import gTTS
from shared_components import get_emoji_title, render_emoji_title_header, get_emoji_link_text, render_footer

# ---- All dashboard.py functions below (copied verbatim for reuse) ----

def dashboard_info():
    """Display the main header and hero section"""
    st.title("📊 interactive dashboard for you to")
    st.title("🔎 discover the stories behind the data")
    # st.markdown("""
    #     **🔎 Discover the stories behind the data.** """)
    st.markdown("""
    Navigate through our sentiment analysis dashboard to explore how public opinion from ***tweets and official news***
    correlates with [S&P 500 as economic indicator](https://www.investing.com/indices/us-spx-500-historical-data) and the [installed solar and wind capacity](https://ember-energy.org/data/monthly-wind-and-solar-capacity-data/). Scroll down to generate your custom report (text and audio) based on the data you chose to plot.""")
    st.markdown("---")

def interactive_dashboard():
    """Content for Dashboard page"""
    import os
    
    # Try multiple methods to get the API key
    api_key_from_secrets = None
    
    # Method 1: Try secrets.toml
    try:
        api_key_from_secrets = st.secrets["OPENAI_API_KEY"]
    except (KeyError, FileNotFoundError):
        pass
    
    # Method 2: Try environment variable
    if not api_key_from_secrets:
        api_key_from_secrets = os.getenv("OPENAI_API_KEY")
    
    # Method 3: Check if no API key found
    if not api_key_from_secrets:
        st.error("Error: OpenAI API Key not found")
        st.info("Please set your OPENAI_API_KEY in .streamlit/secrets.toml or as an environment variable.")
        st.stop()

    # --- DATA SOURCE ---
    df_twitter = create_df_of_twitter_result()
    df_twitter_events = create_df_of_twitter_result_events()  # Events-specific Twitter data
    df_news = create_df_of_newsarticle_result()
    monthly_sp500 = preprocess_sp500_df()
    df_energy = get_energy_df()
    

    def generate_quarters(start_year, end_year):
        return [f"{year} Q{q}" for year in range(start_year, end_year + 1) for q in range(1, 5)]

    quarters_list = generate_quarters(2022, 2024)

    
    # Set default values when quarter selectors are hidden
    selected_start = quarters_list[0]  # First quarter (2022 Q1)
    selected_end = quarters_list[-1]   # Last quarter (2024 Q4)

    def quarter_to_dates(q_str):
        year, q = map(int, q_str.split(" Q"))
        start_month = (q - 1) * 3 + 1
        end_month = start_month + 2
        start_date = pd.to_datetime(f"{year}-{start_month:02d}-01")
        end_date = pd.to_datetime(f"{year}-{end_month:02d}-01") + pd.offsets.MonthEnd(1)
        return start_date, end_date

    start_date, _ = quarter_to_dates(selected_start)
    _, end_date = quarter_to_dates(selected_end)
    if start_date > end_date:
        st.error("Start quarter must be before end quarter.")
        st.stop()

    filtered_sp500 = monthly_sp500[(monthly_sp500['month'] >= start_date) & (monthly_sp500['month'] <= end_date)]

    fig = go2.Figure()

    fig.add_trace(go2.Scatter(
        x=filtered_sp500['month'], y=filtered_sp500['Price'],
        name='S&P 500',
        yaxis='y1',
        mode='lines',
        line=dict(color='blue')
    ))

    df_energy['Date'] = pd.to_datetime(df_energy['Date'])
    filtered_df_energy = df_energy[(df_energy['Date'] >= start_date) & (df_energy['Date'] <= end_date)]

    fig.add_trace(go2.Scatter(
        x=filtered_df_energy['Date'], y=filtered_df_energy['Installed Capacity'],
        name='Installed Capacity Solar + Wind (MW)',
        yaxis='y2',
        mode='lines',
        line=dict(color='green'),
    ))

    df_news['date'] = pd.to_datetime(df_news['date'])
    df_news_filtered = df_news[(df_news['date'] >= start_date) & (df_news['date'] <= end_date)].copy()
    df_news_filtered['date'] = pd.to_datetime(df_news_filtered['date'])
    df_news_filtered['month'] = df_news_filtered['date'].dt.to_period('M').dt.to_timestamp()
    df_news_filtered['correct_prob'] = df_news_filtered[['pos_score', 'neg_score']].max(axis=1)

    monthly_stats_news = df_news_filtered.groupby('month').agg(
        mean_correct_prob=('correct_prob', 'mean'),
        mean_pos_score=('pos_score', 'mean'),
        count=('correct_prob', 'count'),
        std_correct_prob=('correct_prob', 'std'),
    ).reset_index()
    monthly_stats_news['std_correct_prob'] = monthly_stats_news['std_correct_prob'].fillna(0)

    fig.add_trace(go2.Scatter(
        x=monthly_stats_news['month'],
        y=monthly_stats_news['mean_correct_prob'],
        mode='markers',
        marker=dict(
            size=monthly_stats_news['count'] / 3,
            sizemode='area',
            sizeref=2. * monthly_stats_news['count'].max() / (40. ** 2),
            sizemin=4,
            color=monthly_stats_news['mean_pos_score'],
            colorscale='RdYlGn',
            cmin=0.4,
            cmax=0.8,
            showscale=True,
            colorbar=dict(
                title='Mean Pos-score',
                x=0.5,
                y=1.15,
                xanchor='center',
                yanchor='top',
                orientation='h',
                len=0.5
            ),
        ),
        name='News Sentiment',
        yaxis='y3',
        customdata=monthly_stats_news[['std_correct_prob', 'mean_pos_score']].values,
        hovertemplate=(
            "<b>Month:</b> %{x|%Y-%m}<br>" +
            "<b>Mean Correct Prob:</b> %{y:.2f}<br>" +
            "<b>Std Dev (Correct Prob):</b> %{customdata[0]:.2f}<br>" +
            "<b>Mean Pos-score:</b> %{customdata[1]:.2f}<br>" +
            "<b>News Count:</b> %{marker.size}<extra></extra>"
        )
    ))

    fig.add_trace(go2.Scatter(
        x=monthly_stats_news['month'],
        y=monthly_stats_news['mean_correct_prob'],
        mode='lines',
        line=dict(
            color='grey',
            width=0,
        ),
        error_y=dict(
            type='data',
            array=monthly_stats_news['std_correct_prob'],
            symmetric=True,
            visible=True,
            color='grey',
            width=1
        ),
        name='Std (News Sentiment)',
        yaxis='y3',
        showlegend=True,
        hoverinfo='skip',
        visible='legendonly'
    ))

    monthly_stats_twitter = monthly_stats_news
    random_offset = np.random.uniform(low=-0.2, high=0.2, size=len(monthly_stats_twitter))
    y_with_offset = monthly_stats_twitter['mean_correct_prob'] + random_offset * monthly_stats_twitter['mean_correct_prob']

    # Set Twitter marker sizes to be proportional but larger
    twitter_size_capped = 12 + (monthly_stats_twitter['count'] / monthly_stats_twitter['count'].max()) * 12
    

# ---- main dashboard ----
def main():   
    st.set_page_config(page_title="Dashboard @ ☀️🔊🍔", page_icon="📊", layout="wide") 
    dashboard_info()
    interactive_dashboard()

    df_news = create_df_of_newsarticle_result()
    df_news['date'] = pd.to_datetime(df_news['date'])
    df_news['month'] = df_news['date'].dt.to_period('M').dt.to_timestamp()
    df_news['correct_prob'] = df_news[['pos_score', 'neg_score']].max(axis=1)

    monthly_stats_news = df_news.groupby('month').agg(
        mean_sentiment=('pos_score', 'mean'),
        count=('correct_prob', 'count'),
        std_sentiment=('correct_prob', 'std'),
    ).reset_index()
    monthly_stats_news['source'] = 'article'

    df_twitter = create_df_of_twitter_result()
    df_twitter_events = create_df_of_twitter_result_events()  # Events-specific Twitter data
    df_twitter['date'] = pd.to_datetime(df_twitter['date'])
    df_twitter['month'] = df_twitter['date'].dt.to_period('M').dt.to_timestamp()
    df_twitter['correct_prob'] = df_twitter[['pos_score', 'neg_score']].max(axis=1)

    monthly_stats_twitter = df_twitter.groupby('month').agg(
        mean_sentiment=('pos_score', 'mean'),
        count=('correct_prob', 'count'),
        std_sentiment=('correct_prob', 'std'),
    ).reset_index()
    monthly_stats_twitter['source'] = 'tweet'

    df = pd.concat([monthly_stats_twitter, monthly_stats_news])

    def sentiment_color(val):
        # Map sentiment from 0-1 range: 0=red, 1=green
        r = int(255 * (1 - val))  # Red decreases as sentiment increases
        g = int(255 * val)        # Green increases as sentiment increases
        return f'rgb({r},{g},100)'

    GLOBAL_EVENTS = {
        "Russian invasion of Ukraine": "2022-02-24",
        "EU announces REPowerEU plan": "2022-05-18",
        "US Inflation Reduction Act signed (major climate/energy provisions)": "2022-08-16",
        "IEA: global solar power generation surpasses oil for the first time": "2023-04-20",
        "Global installed solar PV capacity surpasses 1 terawatt milestone": "2023-11-30",
        "COP28 concludes with historic agreement to transition away from fossil fuels": "2023-12-13"
    }
    EVENT_DATES = {event: pd.to_datetime(date) for event, date in GLOBAL_EVENTS.items()}
    SHORT_EVENT_LABELS = {
        "Russian invasion of Ukraine": "Russia Invasion",
        "EU announces REPowerEU plan": "REPowerEU Plan",
        "US Inflation Reduction Act signed (major climate/energy provisions)": "US IRA Signed",
        "IEA: global solar power generation surpasses oil for the first time": "Solar>Oil IEA",
        "Global installed solar PV capacity surpasses 1 terawatt milestone": "1TW Solar PV",
        "COP28 concludes with historic agreement to transition away from fossil fuels": "COP28 Fossil Fuels"
    }

    def generate_metric_data(months):
        metrics = {
            'Solar Investment': np.random.normal(100, 10, len(months)),
            'Oil Investment': np.random.normal(80, 15, len(months)),
            'Renewable Energy Jobs': np.random.normal(50, 5, len(months)),
            'Carbon Emissions': np.random.normal(200, 20, len(months))
        }
        return pd.DataFrame({
            'month': months,
            **metrics
        })

    st.markdown("""
    - **Circles**: Articles  
    - **Rhombi**: Tweets  
    - **Y-axis**: Sentiment consensus (higher = more agreement, lower = more disagreement)  
    - **Color**: Red (negative) to Green (positive)  
    - **Size**: Number of texts (articles/tweets)  
    """)

    months = df['month'].dt.strftime('%Y-%m').unique()
    
    selected_event = st.sidebar.selectbox(
        "Select Global Event:",
        options=["None"] + [f"{date.strftime('%Y-%m-%d')} {event}" for event, date in EVENT_DATES.items()]
    )

    selected_metrics = st.sidebar.multiselect(
        "Select metrics to overlay:",
        options=['S&P 500', 'Installed Capacity Renewables'],
        default=[]
    )

    show_animation = st.sidebar.checkbox("Animate monthly data", value=False)


    if selected_event and selected_event != "None":
        event_name_only = selected_event.split(' ', 1)[1] if ' ' in selected_event else selected_event
        event_date = pd.to_datetime(GLOBAL_EVENTS[event_name_only])
        start_date = event_date - pd.Timedelta(days=1)
        end_date = event_date + pd.Timedelta(days=1)
        
        # Use events-specific data for the selected event
        # Filter Twitter events data
        df_twitter_events['date'] = pd.to_datetime(df_twitter_events['date']).dt.tz_convert(None)
        df_twitter_filtered = df_twitter_events[(df_twitter_events['date'] >= start_date) & (df_twitter_events['date'] <= end_date)].copy()
        df_twitter_filtered['date'] = pd.to_datetime(df_twitter_filtered['date'])
        df_twitter_filtered['hour'] = df_twitter_filtered['date'].dt.to_period('H').dt.to_timestamp()
        df_twitter_filtered['correct_prob'] = df_twitter_filtered[['pos_score', 'neg_score']].max(axis=1)
        
        # Aggregate Twitter by hour for events
        hourly_stats_twitter = df_twitter_filtered.groupby('hour').agg(
            mean_sentiment=('pos_score', 'mean'),
            count=('correct_prob', 'count'),
            std_sentiment=('correct_prob', 'std'),
        ).reset_index()
        hourly_stats_twitter['source'] = 'tweet'
        hourly_stats_twitter = hourly_stats_twitter.rename(columns={'hour': 'month'})
        
        # Filter News data
        df_news['date'] = pd.to_datetime(df_news['date'])
        df_news_filtered = df_news[(df_news['date'] >= start_date) & (df_news['date'] <= end_date)].copy()
        df_news_filtered['correct_prob'] = df_news_filtered[['pos_score', 'neg_score']].max(axis=1)
        
        # Aggregate News by day for events
        daily_stats_news = df_news_filtered.groupby('date').agg(
            mean_sentiment=('pos_score', 'mean'),
            count=('correct_prob', 'count'),
            std_sentiment=('correct_prob', 'std'),
        ).reset_index()
        daily_stats_news['source'] = 'article'
        daily_stats_news = daily_stats_news.rename(columns={'date': 'month'})
        
        # Combine Twitter and News data for events
        df_window = pd.concat([hourly_stats_twitter, daily_stats_news])
        
        months_dt = pd.to_datetime(months, format='%Y-%m')
        start_idx = np.searchsorted(months_dt, start_date, side='left')
        end_idx = np.searchsorted(months_dt, end_date, side='right') - 1
        start_idx = max(0, start_idx)
        end_idx = min(len(months) - 1, end_idx)
    else:
        start_idx, end_idx = st.select_slider(
            "Select monthly time window:",
            options=list(range(len(months))),
            value=(0, len(months)-1),
            format_func=lambda x: months[x]
        )
        df_window = df[(df['month'] >= pd.to_datetime(months[start_idx])) & (df['month'] <= pd.to_datetime(months[end_idx]))]

    months_with_data = []
    if not df_window.empty:
        months_with_data = sorted(set(
            df_window[df_window['source'] == 'article']['month'].unique().tolist() +
            df_window[df_window['source'] == 'tweet']['month'].unique().tolist()
        ))


    monthly_sp500 = preprocess_sp500_df()
    df_energy = get_energy_df()
    df_energy = df_energy.rename(columns={'Date': 'month'})
    metric_df = pd.merge(monthly_sp500, df_energy, on='month', how='outer')
    metric_df = metric_df.rename(columns={'Price': 'S&P 500',
                                         'Installed Capacity': 'Installed Capacity Renewables'})
    fig = go.Figure()
    for source, shape in zip(['article', 'tweet'], ['circle', 'diamond']):
        fig.add_trace(go.Scatter(
            x=[], 
            y=[],
            mode='markers',
            marker=dict(
                size=[],
                color=[],
                symbol=shape,
                line=dict(width=1, color='black'),
                opacity=1.0
            ),
            name=source.capitalize(),
            legendgroup=source,
            showlegend=True,
            text=[],
            hoverinfo='text',
        ))
    colors = ['blue', 'red', 'green', 'purple', 'orange', 'brown']
    if show_animation:
        for metric_idx, (metric, color) in enumerate(zip(selected_metrics, colors)):
            trace_yaxis_value = f'y{metric_idx + 2}'
            fig.add_trace(go.Scatter(
                x=[],
                y=[],
                mode='lines',
                name=metric,
                line=dict(color=color),
                yaxis=trace_yaxis_value,
                showlegend=True,
                legendgroup=metric
            ))
    if not show_animation:
        for source_idx, (source, shape) in enumerate(zip(['article', 'tweet'], ['circle', 'diamond'])):
            d_all_data = df_window[df_window['source'] == source]
            fig.data[source_idx].x = d_all_data['month'].tolist() if not d_all_data.empty else []
            fig.data[source_idx].y = d_all_data['std_sentiment'].tolist() if not d_all_data.empty else []
            if shape == 'diamond':  # Twitter symbols
                fig.data[source_idx].marker.size = [12 + (cnt/d_all_data['count'].max())*12 for cnt in d_all_data['count']] if not d_all_data.empty else []
            else:  # News symbols
                fig.data[source_idx].marker.size = np.sqrt(d_all_data['count'])*3 if not d_all_data.empty else []
            fig.data[source_idx].marker.color = [sentiment_color(v) for v in d_all_data['mean_sentiment']] if not d_all_data.empty else []
            fig.data[source_idx].text = [
                f"{source.capitalize()}<br>Month: {m.strftime('%Y-%m')}<br>Mean Sentiment: {s:.2f}<br>Consensus: {c:.2f}<br>Count: {cnt}" 
                for m, s, c, cnt in zip(d_all_data['month'], d_all_data['mean_sentiment'], d_all_data['std_sentiment'], d_all_data['count'])
            ] if not d_all_data.empty else []
    elif months_with_data:
        first_month = months_with_data[0]
        for source_idx, (source, shape) in enumerate(zip(['article', 'tweet'], ['circle', 'diamond'])):
            d_first_month = df_window[(df_window['source'] == source) & (df_window['month'] <= first_month)]
            fig.data[source_idx].x = d_first_month['month'].tolist() if not d_first_month.empty else []
            fig.data[source_idx].y = d_first_month['std_sentiment'].tolist() if not d_first_month.empty else []
            if shape == 'diamond':  # Twitter symbols
                fig.data[source_idx].marker.size = [12 + (cnt/d_first_month['count'].max())*12 for cnt in d_first_month['count']] if not d_first_month.empty else []
            else:  # News symbols
                fig.data[source_idx].marker.size = np.sqrt(d_first_month['count'])*3 if not d_first_month.empty else []
            marker_colors = []
            marker_opacities = []
            if not d_first_month.empty:
                for i, row in d_first_month.iterrows():
                    marker_colors.append(sentiment_color(row['mean_sentiment']))
                    if row['month'] < first_month:
                        marker_opacities.append(0.3)
                    else:
                        marker_opacities.append(1.0)
            fig.data[source_idx].marker.color = marker_colors
            fig.data[source_idx].marker.opacity = marker_opacities
            fig.data[source_idx].text = [
                f"{source.capitalize()}<br>Month: {m.strftime('%Y-%m')}<br>Mean Sentiment: {s:.2f}<br>Consensus: {c:.2f}<br>Count: {cnt}" 
                for m, s, c, cnt in zip(d_first_month['month'], d_first_month['mean_sentiment'], d_first_month['std_sentiment'], d_first_month['count'])
            ] if not d_first_month.empty else []
        for metric_idx, (metric, color) in enumerate(zip(selected_metrics, colors)):
            metric_trace_idx = 2 + metric_idx
            if metric_trace_idx < len(fig.data):
                d_metric_first_month = metric_df[metric_df['month'] <= first_month]
                fig.data[metric_trace_idx].x = d_metric_first_month['month'].tolist() if not d_metric_first_month.empty else []
                fig.data[metric_trace_idx].y = d_metric_first_month[metric].tolist() if not d_metric_first_month.empty else []

    metric_yaxis_layout_config = {}
    current_plot_yaxis_id = 2
    for metric, color in zip(selected_metrics, colors):
        layout_axis_key = f'yaxis{current_plot_yaxis_id}'
        trace_yaxis_value = f'y{current_plot_yaxis_id}'
        metric_yaxis_layout_config[layout_axis_key] = dict(
            title=metric,
            overlaying='y',
            side='right',
            showgrid=False,
            automargin=True,
            anchor='free',
            position=1 - (0.07 * (current_plot_yaxis_id - 1))
        )
        if not show_animation:
            # Filter metric data to match the time window
            filtered_metric_df = metric_df[(metric_df['month'] >= pd.to_datetime(months[start_idx])) & (metric_df['month'] <= pd.to_datetime(months[end_idx]))]
            fig.add_trace(go.Scatter(
                x=filtered_metric_df['month'],
                y=filtered_metric_df[metric],
                mode='lines',
                name=metric,
                line=dict(color=color),
                yaxis=trace_yaxis_value,
                showlegend=True,
                legendgroup=metric
            ))
        current_plot_yaxis_id += 1

    if selected_event and selected_event != "None" and not df_window.empty:
        event_name_only = selected_event.split(' ', 1)[1] if ' ' in selected_event else selected_event
        event_date = pd.to_datetime(GLOBAL_EVENTS[event_name_only])
        x_type = type(df_window['month'].iloc[0])
        event_month = pd.Timestamp(event_date.year, event_date.month, 1)
        event_month = x_type(event_month)
        x_min = df_window['month'].min()
        x_max = df_window['month'].max()
        if x_min <= event_month <= x_max:
            fig.add_vline(
                x=event_month,
                line_width=2,
                line_dash="dash",
                line_color="red",
                annotation_text=selected_event,
                annotation_position="top"
            )
    elif selected_event and selected_event != "None" and df_window.empty:
        st.warning("No data available for the selected event window.")

    if show_animation:
        frames = []
        for m_idx, m in enumerate(months_with_data):
            frame_updates_for_traces = []
            for source_idx, (source, shape) in enumerate(zip(['article', 'tweet'], ['circle', 'diamond'])):
                d_for_frame = df_window[(df_window['source'] == source) & (df_window['month'] <= m)]
                marker_colors = []
                marker_opacities = []
                if not d_for_frame.empty:
                    for i, row in d_for_frame.iterrows():
                        marker_colors.append(sentiment_color(row['mean_sentiment']))
                        if row['month'] < m:
                            marker_opacities.append(0.3)
                        else:
                            marker_opacities.append(1.0)
                frame_updates_for_traces.append({
                    'x': d_for_frame['month'].tolist() if not d_for_frame.empty else [],
                    'y': d_for_frame['std_sentiment'].tolist() if not d_for_frame.empty else [],
                    'marker': {
                        'size': [12 + (cnt/d_for_frame['count'].max())*12 for cnt in d_for_frame['count']] if shape == 'diamond' and not d_for_frame.empty else (np.sqrt(d_for_frame['count'])*3 if not d_for_frame.empty else []),
                        'color': marker_colors,
                        'symbol': shape,
                        'line': dict(width=1, color='black'),
                        'opacity': marker_opacities
                    },
                    'text': [
                        f"{source.capitalize()}<br>Month: {mo.strftime('%Y-%m')}<br>Mean Sentiment: {s:.2f}<br>Consensus: {c:.2f}<br>Count: {cnt}" 
                        for mo, s, c, cnt in zip(d_for_frame['month'], d_for_frame['mean_sentiment'], d_for_frame['std_sentiment'], d_for_frame['count'])
                    ] if not d_for_frame.empty else [],
                })
            for metric_idx, (metric, color) in enumerate(zip(selected_metrics, colors)):
                metric_trace_idx = 2 + metric_idx
                d_metric_for_frame = metric_df[metric_df['month'] <= m]
                frame_updates_for_traces.append({
                    'x': d_metric_for_frame['month'].tolist() if not d_metric_for_frame.empty else [],
                    'y': d_metric_for_frame[metric].tolist() if not d_metric_for_frame.empty else [],
                })
            frames.append(go.Frame(data=frame_updates_for_traces, name=str(m)))
        if frames:
            fig.frames = frames
            fig.update_layout(
                updatemenus=[{
                    "type": "buttons",
                    "buttons": [
                        {
                            "label": "Play",
                            "method": "animate",
                            "args": [
                                None, 
                                {
                                    "frame": {"duration": 500, "redraw": True}, 
                                    "fromcurrent": True, 
                                    "mode": "immediate"
                                }
                            ],
                            "args2": [
                                [None], 
                                {
                                    "frame": {"duration": 0, "redraw": False}, 
                                    "mode": "immediate"
                                }
                            ],
                        }
                    ]
                }]
            )
        else:
            st.warning("No data available for animation in the selected window.")

    visible_months = df_window['month'].unique()
    if len(visible_months) > 12:
        indices_to_show = np.linspace(0, len(visible_months) - 1, 12, dtype=int)
        display_tickvals = [visible_months[i] for i in indices_to_show]
    else:
        display_tickvals = visible_months

    fig.update_layout(
        xaxis=dict(title='Month', tickformat='%Y-%m', tickvals=display_tickvals),
        yaxis=dict(
            title='Sentiment Consensus (Std Dev)',
            autorange='reversed',
            side='left',
        ),
        legend=dict(title='Source'),
        height=900,
        margin=dict(l=40, r=150, t=60, b=300),
        plot_bgcolor='white',
        **metric_yaxis_layout_config
    )
    if not df_window.empty:
        current_x_min = df_window['month'].min()
        current_x_max = df_window['month'].max()
    else:
        current_x_min = None
        current_x_max = None
    for event_name_full, event_date in EVENT_DATES.items():
        if current_x_min and current_x_max and current_x_min <= event_date <= current_x_max:
            fig.add_annotation(
                x=event_date,
                y=-0.05,
                xref="x",
                yref="paper",
                text=SHORT_EVENT_LABELS.get(event_name_full, event_name_full),
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor="darkgrey",
                ax=0,
                ay=100,
                textangle=-90,
                valign="bottom",
                font=dict(color="darkgrey", size=10)
            )
    st.plotly_chart(fig, use_container_width=True)
    
    # --- TEXT GENERATION AND AUDIO ---
    
    # Get the actual date range from the slider
    start_month_str = months[start_idx] if start_idx < len(months) else "N/A"
    end_month_str = months[end_idx] if end_idx < len(months) else "N/A"
    st.write(f"**Analysis Period:** {start_month_str} to {end_month_str}")
    
    # Initialize session state for generated text
    if 'generated_text' not in st.session_state:
        st.session_state.generated_text = ""
    
    # Show what will be included in the report
    st.subheader("📋 AI Report Configuration")
    st.write("**Time Period:** {} to {}".format(months[start_idx], months[end_idx]))
    
    if selected_metrics:
        st.write("**📊 Metrics to include:**")
        for metric in selected_metrics:
            st.write(f"  • {metric}")
    else:
        st.write("**📊 Metrics:** Only sentiment data (no economic/capacity metrics selected)")
    
    # Show relevant events
    start_date_preview = pd.to_datetime(months[start_idx])
    end_date_preview = pd.to_datetime(months[end_idx])
    preview_events = []
    
    for event_name, event_date_str in GLOBAL_EVENTS.items():
        event_date = pd.to_datetime(event_date_str)
        if start_date_preview <= event_date <= end_date_preview:
            preview_events.append(f"{event_date_str}: {event_name}")
    
    if preview_events:
        st.write("**🌍 Global events in this period:**")
        for event in preview_events:
            st.write(f"  • {event}")
    else:
        st.write("**🌍 Global events:** No major events in selected timeframe")
    
    # Button to generate text report
    if st.button("⚙️ Generate AI Report"):
        try:
            # Filter data for the selected period for text generation
            filtered_news_for_text = df_news[(df_news['month'] >= pd.to_datetime(months[start_idx])) & (df_news['month'] <= pd.to_datetime(months[end_idx]))]
            filtered_twitter_for_text = df_twitter[(df_twitter['month'] >= pd.to_datetime(months[start_idx])) & (df_twitter['month'] <= pd.to_datetime(months[end_idx]))]
            
            # Aggregate the filtered data for text generation
            monthly_stats_news_text = filtered_news_for_text.groupby('month').agg(
                mean_sentiment=('pos_score', 'mean'),
                count=('correct_prob', 'count'),
                std_sentiment=('correct_prob', 'std'),
            ).reset_index()
            
            monthly_stats_twitter_text = filtered_twitter_for_text.groupby('month').agg(
                mean_sentiment=('pos_score', 'mean'),
                count=('correct_prob', 'count'),
                std_sentiment=('correct_prob', 'std'),
            ).reset_index()
            
            # Only include metrics data if they are selected for display
            filtered_sp500_text = pd.DataFrame()  # Empty by default
            filtered_energy_text = pd.DataFrame()  # Empty by default
            
            if 'S&P 500' in selected_metrics:
                filtered_sp500_text = monthly_sp500[(monthly_sp500['month'] >= pd.to_datetime(months[start_idx])) & (monthly_sp500['month'] <= pd.to_datetime(months[end_idx]))]
            
            if 'Installed Capacity Renewables' in selected_metrics:
                filtered_energy_text = df_energy[(df_energy['month'] >= pd.to_datetime(months[start_idx])) & (df_energy['month'] <= pd.to_datetime(months[end_idx]))]
            
            # Filter events that fall within the selected timeframe
            start_date_period = pd.to_datetime(months[start_idx])
            end_date_period = pd.to_datetime(months[end_idx])
            relevant_events = []
            
            for event_name, event_date_str in GLOBAL_EVENTS.items():
                event_date = pd.to_datetime(event_date_str)
                if start_date_period <= event_date <= end_date_period:
                    relevant_events.append(f"{event_date_str} {event_name}")
            
            result_text = create_text_from_sent_analy_df(
                monthly_stats_twitter_text, 
                monthly_stats_news_text, 
                filtered_sp500_text, 
                filtered_energy_text,
                selected_metrics,
                relevant_events
            )
            st.session_state.generated_text = result_text
            
            # Show summary of what was included
            included_data = ["Twitter sentiment", "News sentiment"]
            if 'S&P 500' in selected_metrics and not filtered_sp500_text.empty:
                included_data.append("S&P 500 performance")
            if 'Installed Capacity Renewables' in selected_metrics and not filtered_energy_text.empty:
                included_data.append("Renewable capacity data")
            
            st.success(f"✅ AI Report generated successfully! Included: {', '.join(included_data)}")
            if relevant_events:
                st.info(f"📅 Analyzed {len(relevant_events)} event(s) in the selected timeframe")
        except Exception as e:
            st.error(f"Error generating text: {str(e)}")
            st.info("Text generation requires valid data for the selected time period.")
    
    # Display generated text and audio controls if text exists
    if st.session_state.generated_text:
        st.subheader("📝 AI-Generated Sentiment Analysis Report")
        st.write("**Generated Report:**")
        st.write(st.session_state.generated_text)
        
        if st.button("🎧 Generate Audio"):
            if isinstance(st.session_state.generated_text, str) and st.session_state.generated_text.strip():
                tts = gTTS(st.session_state.generated_text.strip(), lang="en")
                tts.save("output.mp3")
                st.audio("output.mp3", format="audio/mp3")
            else:
                st.warning("Generated text is empty or invalid.")

    render_footer()

    
if __name__ == "__main__":
    main()

