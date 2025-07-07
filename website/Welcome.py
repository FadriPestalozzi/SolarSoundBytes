import streamlit as st
from PIL import Image
import glob
import os
import time
from shared_components import get_emoji_title, render_emoji_title_header, get_emoji_link_text, render_footer

def main():
    # What is SolarSoundBytes?
    """Main function for the welcome page"""
    st.set_page_config(page_title="SolarSoundBytes = ☀️🔊🍔", page_icon="🤗", layout="wide")

    # Mobile device warning - only shows on small screens
    st.markdown("""
    <style>
    .mobile-warning {
        display: none;
        background-color: #ff4b4b;
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        text-align: center;
        font-weight: bold;
        border-left: 5px solid #ff6b47;
    }
    
    @media only screen and (max-width: 768px) {
        .mobile-warning {
            display: block;
        }
    }
    </style>
    
    <div class="mobile-warning">
        📱➡️💻 <strong>Mobile Device Detected!</strong><br><br>
        For the best user experience with ☀️Solar🔊Sound🍔Bytes, please use a desktop or laptop computer with mouse navigation. 
        The interactive dashboard can be challenging to navigate on touch devices. 🖱️
        <br><br>
        Thank you for understanding! 🤗
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"<h1 style='text-align: center'>What are {get_emoji_title()}?</h1>", unsafe_allow_html=True)

    st.markdown(f"""
    • Ever wondered what people really think about solar panels and wind turbines? ♻️ <br>
    • And how official news coverage on renewable energy compares with the general public's attitude? 📰<br>
    • This project lets you dive into the world of renewable energy sentiment - no technical knowledge required! 🤗<br>
    """, unsafe_allow_html=True)

    # Why was this tool created?
    st.markdown("<h2>🎯 Why was this tool created?</h2>", unsafe_allow_html=True)
        
    st.markdown(f"""
    [We](Meet_the_Team) created {get_emoji_title()} to empower you to investigate and draw your own conclusions about the ongoing transition towards a more sustainable energy system. 🔎 
    
    We want to bridge the gap between public perception and media coverage of renewable energy, making complex sentiment analysis accessible to everyone - no technical knowledge required! 🤗
    
    Since this covers a lot of ground 🙊 let's dive into <a href="#what-can-you-do-with-this-tool">what you can do</a>, <a href="#how-does-it-work">how this works</a> and <a href="#your-workflow">your workflow</a> to prevent further <a href="https://en.wiktionary.org/wiki/brainfuck" target="_blank">brainfuck</a>! 🤯
    """, unsafe_allow_html=True)
    
    # What can you do with this tool?
    st.markdown("<h2>🔍 What can you do with this tool?</h2>", unsafe_allow_html=True)
    st.markdown("""
    **Explore sentiment trends**: <br>
    Discover how public opinion around renewable energy and energy storage evolved by comparing: <br>
    • General public discussions ([Twitter / X](https://en.wikipedia.org/wiki/Twitter)) <br>
    • Official news coverage ([GNews](https://gnews.io/)) <br>
    
    **Add context with market data**: <br>
    Enhance your analysis by overlaying: <br>
    • [S&P 500 market performance](https://www.investing.com/indices/us-spx-500-historical-data) <br>
    • [Global Wind and Solar Capacity Data](https://ember-energy.org/data/monthly-wind-and-solar-capacity-data/) <br>
    
    **Generate insights**: <br>
    Use our [interactive dashboard](Interactive_Dashboard) to: <br>
    • customize your data range <br>
    • create AI-driven summaries <br>
    • and export your findings as audio SoundBytes <br>
    • to create your own podcast on this hot topic! 🔥
    """, unsafe_allow_html=True)

    # How does it work?
    st.markdown("<h2>⚙️ How does it work?</h2>", unsafe_allow_html=True)
    st.markdown("""

    1. **Data Collection**: We gathered raw data from Twitter, news sites, plus additional metrics like S&P 500 performance and Ember's Monthly Wind and Solar capacity data
    
    2. **Natural Language Processing (NLP)**: Using advanced NLP techniques, we analyzed sentiment patterns in social media conversations and official news articles to identify trends in public opinion and media coverage
    
    3. **Accessible Tools**: We made this data freely available through user-friendly visualization tools that let you explore correlations, generate AI summaries, and create audio exports
    
    Want to dive deeper into the technical details? Check out our [From Raw Data to Podcasts](From_Raw_Data_to_Podcasts) page for a comprehensive look at our data processing pipeline!

    All analysis covers the same timeframe (2022-01-02 to 2024-12-24) to ensure meaningful comparisons across different data sources.
    """)

    # Your workflow
    st.markdown("<h2>🚀 Your <a href='Interactive_Dashboard'>dashboard</a> workflow</h2>", unsafe_allow_html=True)
    st.markdown("""
    • **Choose your timeframe** - Select the date range you want to analyze <br>
    • **Select your data** - Pick from tweets, news, market and renewable capacity metrics <br>
    • **Explore visual sentiment analysis** - Customize and animate your interactive chart <br>
    • **Generate an AI summary** - Create text and audio summaries of your findings <br>
    """, unsafe_allow_html=True)



        
    # Render the reusable footer
    render_footer()

    # --- Image Carousel ---
    st.markdown("---")
    
    carousel_container = st.container()
    with carousel_container:
        # Get all image files from the welcome-carousel folder and subdirectories
        image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.webp', '*.avif']
        carousel_images = []
        
        for extension in image_extensions:
            # Search in main folder and subdirectories
            carousel_images.extend(glob.glob(f'website/images/welcome-carousel/**/{extension}', recursive=True))
        
        # Filter out directories and validate image files
        valid_images = []
        for img_path in carousel_images:
            if os.path.isfile(img_path):
                try:
                    # Try to open the image to validate it
                    with Image.open(img_path) as img:
                        img.verify()  # Verify it's a valid image
                    valid_images.append(img_path)
                except Exception as e:
                    # Skip invalid/corrupted images
                    print(f"Skipping invalid image: {img_path} - {e}")
                    continue
        
        if valid_images:
            # Initialize session state for carousel index
            if 'carousel_index' not in st.session_state:
                st.session_state.carousel_index = 0

            # Show current image
            current_image = valid_images[st.session_state.carousel_index]
            st.image(current_image, width=200, use_container_width=True)

            # Wait for 5 seconds, then move to next image and rerun
            time.sleep(5)
            st.session_state.carousel_index = (st.session_state.carousel_index + 1) % len(valid_images)
            st.rerun()


if __name__ == "__main__":
    main()
