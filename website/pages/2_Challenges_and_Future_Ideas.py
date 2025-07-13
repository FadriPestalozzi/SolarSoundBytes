import streamlit as st
from PIL import Image
from shared_components import render_footer


def render_limitations():

    # Centered title
    st.title("🚧 Challenges and Future Ideas 🚀")

    st.header("🚧 Challenges & Limitations during our bootcamp")
    st.write("""
        - **Twitter API rate limits and restrictions** on historical data access, which lead us to scrape tweets and create our own dataset.
        - How to **extract location data** from scraped tweets.
        - **No high-quality news artcile dataset** with manually labeled sentiment available to train a model.
        - **Time constraints** limited the scope of development and testing.
        - During multiple rounds of fine-tuning, we observed that the **data was biased** toward positive sentiment,
        which led us to **gather news articles by API calls** and thus create our own dataset instead.
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.header("🚀 Future Ideas")
        
    st.subheader("📱 User Experience & Interface")
    st.write("""
    - **[Issue #41](https://github.com/FadriPestalozzi/SolarSoundBytes/issues/41): Mobile Experience** - Optimize the application for mobile devices and improve responsive design.
    - **[Issue #37](https://github.com/FadriPestalozzi/SolarSoundBytes/issues/37): Add opacity to place graphed data into individual layers** - Enhance data visualization with layered opacity controls for better data exploration.
    - **[Issue #32](https://github.com/FadriPestalozzi/SolarSoundBytes/issues/32): Zoomable colormap with adjustable min-max and color scheme** - Implement interactive colormap controls for better data visualization customization.
    - **[Issue #33](https://github.com/FadriPestalozzi/SolarSoundBytes/issues/33): Representative symbol size in legend with article/tweet counts** - Improve legend clarity with proportional symbol sizing based on data counts.
    """)
    
    st.subheader("🗄️ Data Management & Processing")
    st.write("""
    - **[Issue #36](https://github.com/FadriPestalozzi/SolarSoundBytes/issues/36): Build SQL database from JSON files** - Migrate from JSON file storage to a proper SQL database for better performance and scalability.
    - **[Issue #31](https://github.com/FadriPestalozzi/SolarSoundBytes/issues/31): Add character count columns to datasets** - Enhance datasets with character count metrics for more detailed text analysis.
    - **[Issue #30](https://github.com/FadriPestalozzi/SolarSoundBytes/issues/30): Add country of origin column to datasets** - Include geographical metadata to enable location-based sentiment analysis.
    """)
    
    st.subheader("📊 Data Visualization & Analysis")
    st.write("""
    - **[Issue #34](https://github.com/FadriPestalozzi/SolarSoundBytes/issues/34): Symbol size ~ number of characters (not number of articles/tweets)** - Adjust visualization scaling to reflect content volume rather than item count.
    """)
    
    st.subheader("🚀 Advanced Features")
    st.write("""
    - **Model Training and Fine-Tuning** specifically tailored for renewable energy discourse to improve the relevance and accuracy of input data.
    - **Live Data Integration:** Implement real-time data pipelines for continuous sentiment analysis and regular updates on renewable energy metrics.
    - **Audio Podcast Experience:** Enhance audio quality and develop a podcast with background music integration and multi-language support.
    """, unsafe_allow_html=True)


def main():
    """Main function to run the page"""
    st.set_page_config(page_title="Challenges & WIP @ ☀️🔊🍔", page_icon="🚧", layout="wide")
    render_limitations()
    render_footer()

if __name__ == "__main__":
    main() 