# --- Imports from sentiment_viz.py and dashboard.py merged ---
import streamlit as st
import plotly.graph_objs as go
import plotly.graph_objects as go2
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime, timedelta

# Add paths for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data_analysis'))

from import_twitter_sent_analysis import create_df_of_twitter_result, create_df_of_twitter_result_events
from import_newsarticle_sent_analysis import create_df_of_newsarticle_result
from process_sp500_df import preprocess_sp500_df
from import_energy_data import get_energy_df
from text_creation.create_text import create_text_from_sent_analy_df
from gtts import gTTS
from shared_components import get_emoji_title, render_emoji_title_header, get_emoji_link_text, render_footer

# ---- All dashboard.py functions below (copied verbatim for reuse) ----

def dashboard_info():
    """Display the main header and hero section"""
    st.title("🔍 Investigate Sentiment Towards Renewables")
    st.markdown("""    
    To explore how public opinion about renewable energy from tweets and official news articles correlates with market indicators ([S&P 500](https://www.investing.com/indices/us-spx-500-historical-data)) 
    and installed renewable energy capacity ([installed solar and wind capacity](https://ember-energy.org/data/monthly-wind-and-solar-capacity-data/)) this interactive dashboard enables you to: 
    - select a custom time period or a global event at a specific date ⏳
    - choose which additional metrics to overlay 📈
    - generate an AI-summary of your customized data selection and convert that summary into an audio file, i.e. your very own podcast 🔊
    """)
    

def interactive_dashboard():
    """Content for Dashboard page"""

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
            opacity=0.5,
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
    st.set_page_config(page_title="Interactive Dashboard @ ☀️🔊🍔", page_icon="📊", layout="wide") 
    dashboard_info()
    
    # Add CSS for sticky timeframe selector
    st.markdown("""
    <style>
    .sticky-timeframe {
        position: sticky;
        top: 0;
        z-index: 999;
        background-color: white;
        padding: 15px 0;
        margin-bottom: 10px;
    }
    .chart-legend-spacing {
        margin-top: 10px;
    }
    /* General button styles - exclude primary buttons */
    .stButton > button:not([kind="primary"]) {
        background: transparent !important;
        background-color: transparent !important;
        background-image: none !important;
        color: black !important;
        font-size: 4em !important;
        font-weight: bold !important;
        padding: 24px 48px !important;
        box-shadow: none !important;
    }
    .stButton > button:not([kind="primary"]):hover {
        background: transparent !important;
        background-color: transparent !important;
        background-image: none !important;
        box-shadow: none !important;
    }
    /* Specific styling for the SoundByte Summary button - multiple selectors for maximum compatibility */
    div[data-testid="stButton"] button[kind="primary"],
    div[data-testid="stButton"] button[kind="primary"] p,
    div[data-testid="stButton"] button[kind="primary"] span,
    .stButton button[kind="primary"],
    .stButton button[kind="primary"] p,
    .stButton button[kind="primary"] span {
        background: linear-gradient(45deg, #667eea, #764ba2) !important;
        background-color: #667eea !important;
        color: white !important;
        border: none !important;
        font-size: 3.0rem !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    /* Hover styles - keep gradient background but add red border */
    div[data-testid="stButton"] button[kind="primary"]:hover,
    .stButton button[kind="primary"]:hover{
        border: 12px solid red !important;
        color: white !important;
    }
    /* Fix button edges and match input sizing */
    button[kind="primary"] {
        font-size: 3.0rem !important;
        outline: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Load data first
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
    
    # Generate months list for timeframe selector
    months = df['month'].dt.strftime('%Y-%m').unique()
    
    # Define GLOBAL_EVENTS for use throughout the function
    GLOBAL_EVENTS = {
        "Russian invasion of Ukraine": "2022-02-24",
        "EU announces REPowerEU plan": "2022-05-18",
        "US Inflation Reduction Act signed (major climate/energy provisions)": "2022-08-16",
        "IEA: global solar power generation surpasses oil for the first time": "2023-04-20",
        "Global installed solar PV capacity surpasses 1 terawatt milestone": "2023-11-30",
        "COP28 concludes with historic agreement to transition away from fossil fuels": "2023-12-13"
    }
    EVENT_DATES = {event: pd.to_datetime(date) for event, date in GLOBAL_EVENTS.items()}
    
    # ===== STICKY TIMEFRAME SELECTOR =====
    with st.container():
        st.markdown('<div class="sticky-timeframe">', unsafe_allow_html=True)
        st.subheader("⚙️ Choose Data to Analyze")
        
        # Create two columns for the selection options
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.write("**⏳ Option 1: Choose Custom Time Period**")
            start_idx, end_idx = st.select_slider(
                "Select timeframe:",
                options=list(range(len(months))),
                value=(0, len(months)-1),
                format_func=lambda x: months[x],
                help="Select the start and end months for your analysis"
            )
            
            # Add metrics selector below timeframe for Option 1
            st.write("**📈 Additional Metrics (Monthly Data)**")
            selected_metrics = st.multiselect(
                "Select metrics to overlay: (optional)",
                options=['S&P 500', 'Installed Capacity Renewables'],
                default=[],
                help="These monthly metrics will be overlaid with sentiment data for trend analysis"
            )
        
        with col2:
            st.write("**🌍 Option 2: Choose Global Event**")
            selected_event = st.selectbox(
                "Select Global Event:",
                options=["None"] + [f"{date} {event}" for event, date in GLOBAL_EVENTS.items()],
                help="Choose a global event to analyze sentiment around that specific date (overwrites timeframe selection)"
            )
        
        # Chart legend spanning both columns
        st.markdown('<div class="chart-legend-spacing">', unsafe_allow_html=True)
        st.subheader("📊 Chart Legend")
        
        # Create two columns for the legend with narrower first column
        legend_col1, legend_col2 = st.columns([1, 2])
        
        with legend_col1:
            st.markdown("""
            - **Circles**: News Articles  
            - **Rhombi**: Tweets
            - **Color:** Red (negative) to Green (positive)  
            - **Size:** Number of texts (articles/tweets)  
            """)
        
        with legend_col2:
            st.markdown("""
            - **X-axis**: Time
            - **Y-axis (primary, left)**: Sentiment consensus (higher = more agreement within aggregated data)  
            - **Y-axis (secondary, right)**: Optional metrics (e.g. S&P 500, installed capacity)
            """)
            
        # Add combined metrics information below chart legend after selected_event is defined
        if selected_event and selected_event != "None":
            st.info("🔒 For event analysis, only sentiment data is displayed. Monthly metrics are hidden when zooming into specific events.")
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close chart-legend-spacing
        st.markdown('</div>', unsafe_allow_html=True)  # Close sticky-timeframe
    
    # Continue with the old interactive_dashboard logic
    interactive_dashboard()

    def sentiment_color(val):
        # Map sentiment from 0-1 range: 0=red, 1=green
        r = int(255 * (1 - val))  # Red decreases as sentiment increases
        g = int(255 * val)        # Green increases as sentiment increases
        return f'rgb({r},{g},100)'

    # Global events data (now defined in the main timeframe selector above)
    # EVENT_DATES will be created from the GLOBAL_EVENTS defined in the selector
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

    # Sidebar controls (metrics selector moved to main timeframe area)

    # Data filtering based on timeframe selector and event selection
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
        start_idx_event = np.searchsorted(months_dt, start_date, side='left')
        end_idx_event = np.searchsorted(months_dt, end_date, side='right') - 1
        start_idx_event = max(0, start_idx_event)
        end_idx_event = min(len(months) - 1, end_idx_event)
    else:
        # Use the timeframe from the sticky selector above
        df_window = df[(df['month'] >= pd.to_datetime(months[start_idx])) & (df['month'] <= pd.to_datetime(months[end_idx]))]




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
    
    # Add sentiment data to the plot
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

    # Only add metrics for custom time periods, not for events
    metric_yaxis_layout_config = {}
    if not (selected_event and selected_event != "None"):
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
            # Filter metric data for custom time periods only
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



    # Calculate regular tick intervals based on whether event is selected
    if not df_window.empty:
        if selected_event and selected_event != "None":
            # For events, show daily/hourly ticks for precise sentiment analysis
            event_name_only = selected_event.split(' ', 1)[1] if ' ' in selected_event else selected_event
            event_date = pd.to_datetime(GLOBAL_EVENTS[event_name_only])
            start_display = event_date - pd.Timedelta(days=1)
            end_display = event_date + pd.Timedelta(days=1)
            
            # Generate daily ticks for the 3-day event window
            display_tickvals = []
            current_day = start_display
            while current_day <= end_display:
                display_tickvals.append(current_day)
                current_day += pd.Timedelta(days=1)
        else:
            # For custom periods, show monthly ticks
            start_month = pd.to_datetime(months[start_idx])
            end_month = pd.to_datetime(months[end_idx])
            
            # Calculate total months in range
            total_months = (end_month.year - start_month.year) * 12 + (end_month.month - start_month.month) + 1
            
            # Dynamically determine interval to keep around 8-10 ticks
            target_ticks = 9  # Optimal number of ticks
            interval_months = max(1, round(total_months / target_ticks))
            
            # Generate ticks at regular intervals starting from first month
            display_tickvals = []
            current_month = start_month
            while current_month <= end_month:
                display_tickvals.append(current_month)
                # Add the interval months
                if current_month.month + interval_months > 12:
                    next_year = current_month.year + ((current_month.month + interval_months - 1) // 12)
                    next_month = ((current_month.month + interval_months - 1) % 12) + 1
                else:
                    next_year = current_month.year
                    next_month = current_month.month + interval_months
                current_month = pd.Timestamp(year=next_year, month=next_month, day=1)
    else:
        display_tickvals = []

    # Set x-axis format based on whether event is selected
    if selected_event and selected_event != "None":
        x_axis_title = 'Date'
        x_tick_format = '%Y-%m-%d'
    else:
        x_axis_title = 'Month'
        x_tick_format = '%Y-%m'
    
    fig.update_layout(
        xaxis=dict(title=x_axis_title, tickformat=x_tick_format, tickvals=display_tickvals, showgrid=True, gridcolor='lightgray'),
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
    
    # Get the actual date range being plotted (either slider or event window)
    if selected_event and selected_event != "None":
        event_name_only = selected_event.split(' ', 1)[1] if ' ' in selected_event else selected_event
        event_date = pd.to_datetime(GLOBAL_EVENTS[event_name_only])
        start_display_period = event_date - pd.Timedelta(days=1)
        end_display_period = event_date + pd.Timedelta(days=1)
        period_str = f"{start_display_period.strftime('%Y-%m-%d')} to {end_display_period.strftime('%Y-%m-%d')} (3 days around {event_name_only})"
    else:
        start_month_str = months[start_idx] if start_idx < len(months) else "N/A"
        end_month_str = months[end_idx] if end_idx < len(months) else "N/A"
        month_count = end_idx - start_idx + 1
        period_str = f"{start_month_str} to {end_month_str} ({month_count} months)"
    
    # Initialize session state for generated text
    if 'generated_text' not in st.session_state:
        st.session_state.generated_text = ""
    
    # Show what will be included in the report
    st.subheader("📋 AI Report Configuration")
    st.write(f"**Analysis Period:** {period_str}")
    
    if selected_event and selected_event != "None":
        st.write("**📊 Metrics:** Focused on sentiment data only (metrics not displayed for event analysis)")
    elif selected_metrics:
        st.write("**📊 Metrics to include:**")
        for metric in selected_metrics:
            st.write(f"  • {metric}")
    else:
        st.write("**📊 Metrics:** Only sentiment data (no economic/capacity metrics selected)")
    
    # Show relevant events for the actual analysis period
    if selected_event and selected_event != "None":
        event_name_only = selected_event.split(' ', 1)[1] if ' ' in selected_event else selected_event
        event_date = pd.to_datetime(GLOBAL_EVENTS[event_name_only])
        start_date_preview = event_date - pd.Timedelta(days=1)
        end_date_preview = event_date + pd.Timedelta(days=1)
    else:
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
        st.warning("OpenAI API Key not found. To generate AI report, please set your OPENAI_API_KEY in .streamlit/secrets.toml or as an environment variable.")

    # Button to generate text report and audio
    elif st.button("🔊 Generate SoundByte Summary", 
                    type="primary",
                    help="Creates a concise AI summary of your selected timeframe and data, also available as audio."):
        try:
            with st.spinner("Generating your SoundByte summary and audio..."):
                # Filter data for the actual analysis period (either slider range or event window)
                if selected_event and selected_event != "None":
                    event_name_only = selected_event.split(' ', 1)[1] if ' ' in selected_event else selected_event
                    event_date = pd.to_datetime(GLOBAL_EVENTS[event_name_only])
                    text_start_date = event_date - pd.Timedelta(days=1)
                    text_end_date = event_date + pd.Timedelta(days=1)
                    
                    # For events, filter by actual date instead of month
                    filtered_news_for_text = df_news[(df_news['date'] >= text_start_date) & (df_news['date'] <= text_end_date)]
                    filtered_twitter_for_text = df_twitter[(df_twitter['date'] >= text_start_date) & (df_twitter['date'] <= text_end_date)]
                else:
                    # For custom periods, use monthly filtering as before
                    filtered_news_for_text = df_news[(df_news['month'] >= pd.to_datetime(months[start_idx])) & (df_news['month'] <= pd.to_datetime(months[end_idx]))]
                    filtered_twitter_for_text = df_twitter[(df_twitter['month'] >= pd.to_datetime(months[start_idx])) & (df_twitter['month'] <= pd.to_datetime(months[end_idx]))]
                
                # Aggregate the filtered data for text generation
                if selected_event and selected_event != "None":
                    # For events, aggregate by day for news and hour for twitter
                    filtered_news_for_text['day'] = filtered_news_for_text['date'].dt.date
                    monthly_stats_news_text = filtered_news_for_text.groupby('day').agg(
                        mean_sentiment=('pos_score', 'mean'),
                        count=('correct_prob', 'count'),
                        std_sentiment=('correct_prob', 'std'),
                    ).reset_index()
                    monthly_stats_news_text['month'] = pd.to_datetime(monthly_stats_news_text['day'])
                    
                    filtered_twitter_for_text['hour'] = filtered_twitter_for_text['date'].dt.floor('H')
                    monthly_stats_twitter_text = filtered_twitter_for_text.groupby('hour').agg(
                        mean_sentiment=('pos_score', 'mean'),
                        count=('correct_prob', 'count'),
                        std_sentiment=('correct_prob', 'std'),
                    ).reset_index()
                    monthly_stats_twitter_text['month'] = monthly_stats_twitter_text['hour']
                else:
                    # For custom periods, aggregate by month as before
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
                    if selected_event and selected_event != "None":
                        # For events, get the closest monthly data points around the event
                        event_month = pd.Timestamp(text_start_date.year, text_start_date.month, 1)
                        filtered_sp500_text = monthly_sp500[monthly_sp500['month'] == event_month]
                    else:
                        filtered_sp500_text = monthly_sp500[(monthly_sp500['month'] >= pd.to_datetime(months[start_idx])) & (monthly_sp500['month'] <= pd.to_datetime(months[end_idx]))]
                
                if 'Installed Capacity Renewables' in selected_metrics:
                    if selected_event and selected_event != "None":
                        # For events, get the closest monthly data points around the event
                        event_month = pd.Timestamp(text_start_date.year, text_start_date.month, 1)
                        filtered_energy_text = df_energy[df_energy['month'] == event_month]
                    else:
                        filtered_energy_text = df_energy[(df_energy['month'] >= pd.to_datetime(months[start_idx])) & (df_energy['month'] <= pd.to_datetime(months[end_idx]))]
                
                # Filter events that fall within the actual analysis timeframe
                if selected_event and selected_event != "None":
                    start_date_period = text_start_date
                    end_date_period = text_end_date
                else:
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
                
                # Generate audio automatically
                if isinstance(result_text, str) and result_text.strip():
                    tts = gTTS(result_text.strip(), lang="en")
                    tts.save("output.mp3")
                    st.session_state.audio_generated = True
                else:
                    st.session_state.audio_generated = False
                
                # Show summary of what was included
                included_data = ["Twitter sentiment", "News sentiment"]
                if 'S&P 500' in selected_metrics and not filtered_sp500_text.empty:
                    included_data.append("S&P 500 performance")
                if 'Installed Capacity Renewables' in selected_metrics and not filtered_energy_text.empty:
                    included_data.append("Renewable capacity data")
                
                st.success(f"✅ SoundByte Summary generated successfully! Included: {', '.join(included_data)}")
                if relevant_events:
                    st.info(f"📅 Analyzed {len(relevant_events)} event(s) in the selected timeframe")
        except Exception as e:
            st.error(f"Error generating SoundByte: {str(e)}")
            st.info("SoundByte generation requires valid data for the selected time period.")
    
    # Display generated text and audio controls if text exists
    if st.session_state.generated_text:
        st.markdown("---")
        st.markdown("### 📄 Your SoundByte Summary")
        with st.container():
            st.markdown(f"""
            <div style="
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                border-left: 4px solid #667eea;
                margin: 10px 0;
            ">
                {st.session_state.generated_text}
            </div>
            """, unsafe_allow_html=True)
        
        # Audio section
        if hasattr(st.session_state, 'audio_generated') and st.session_state.audio_generated:
            st.markdown("### 🎧 Listen to your SoundByte")
            st.audio("output.mp3", format="audio/mp3")
        else:
            st.info("Audio will be generated automatically with your next SoundByte summary.")

    render_footer()

    
if __name__ == "__main__":
    main()

