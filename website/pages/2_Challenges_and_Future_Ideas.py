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