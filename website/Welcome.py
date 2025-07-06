import streamlit as st
from PIL import Image
import glob
import os
import time
from shared_components import get_emoji_title, render_emoji_title_header, get_emoji_link_text, render_footer

def main():
    """Main function for the welcome page"""
    st.set_page_config(page_title="SolarSoundBytes = ☀️🔊🍔", page_icon="🤗", layout="wide")

    # Create a container for the main content
    main_container = st.container()
    
    with main_container:
        # Header
        st.markdown("<h1 style='text-align: center'>🤗Welcome to</h1>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center'>{get_emoji_title()}</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center'>Mapping our global energy transition into tasty audio-bites</h3>", unsafe_allow_html=True)

        st.markdown("---")

        # Content container with responsive width
        content_container = st.container()
        
        with content_container:
            # What can you do with this tool?
            st.markdown("<h4>🔍 What can you do with this tool?</h4>", unsafe_allow_html=True)
            st.markdown("""
            Ever wondered what people really think about solar panels and wind turbines? 
            And how official news coverage compares to the attitude of the general public? 
            This tool lets you dive into the world of renewable energy sentiment - no technical knowledge required!

            Using Natural Language Processing (NLP), we analyzed Twitter conversations and official news articles for you to visualize trends in public opinion and media coverage around renewable energy.  
            We also compared these trends with key renewable energy indicators including S&P 500 market performance and 
            Ember's Monthly Wind and Solar Capacity Data, all during the same timeframe from 2022-01-02 to 2024-12-24.

            You can explore how public sentiment around renewable energy and energy storage evolves from 2022 to 2024. 
            Compare these trends with key renewable energy indicators including S&P 500 market performance and 
            Ember's Monthly Wind and Solar Capacity Data, all during the same timeframe from 2022-01-02 to 2024-12-24.
            """)

            # Why was this tool created?
            st.markdown("<h4>🎯 Why was this tool created?</h4>", unsafe_allow_html=True)
            st.markdown("""
            [We](Meet_the_Team) created this tool to help you to 🕹️ interactively 🔎 investigate how ♻️ renewable energy is perceived by the general public (Twitter) and how that perception is reflected in official news coverage 📝
            """)
            
            st.markdown("""
            Well that was quite a mouthful 🙊, so let's break it down to prevent further <a href="https://www.tandfonline.com/doi/full/10.1080/07350198.2020.1727096" target="_blank">brainfuck</a> 🤯:
            """, unsafe_allow_html=True)
            
            st.markdown("""
            Our goal is to empower you, the user, to investigate and draw your own conclusions about our ongoing transition to renewable energy.
            """)
            
            st.markdown("For this we:")
            st.markdown("""
            1. Gather raw data from twitter and news sites, as well as additional metrics like economic performance (S&P 500) and installed renewable capacity (Ember's Monthly Wind and Solar)
            2. Make this data publicly accessible for free
            3. Create tools for you to visualize sentiment trends and correlations with additional data, generate AI-driven summaries, and finally export your insights as audio SoundBytes, i.e. create your own podcast on this hot topic 🔥
            """)

            
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
