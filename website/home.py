import streamlit as st
from PIL import Image
import glob
import os
import time
from shared_components import get_emoji_title, render_emoji_title_header, get_emoji_link_text, render_footer

def main():
    """Main function for the home page"""
    st.set_page_config(page_title="SolarSoundBytes = ☀️🔊🍔", page_icon="🤗", layout="wide")

    # Header
    st.markdown(f"<h1 style='text-align: center'>🤗Welcome to {get_emoji_title()}</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center'>Mapping our global energy transition into tasty audio-bites</h3>", unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("""<p style='text-align: left'>
            SolarSoundBytes is a data-driven machine-learning project that explores the relationship between public opinion, media coverage,
            and renewable energy development worldwide.""", unsafe_allow_html=True)
            
    st.markdown("""<p style='text-align: left'>
            Using Natural Language Processing (NLP) sentiment analysis of Twitter conversations and official news coverage,
            we analyze correlations with key renewable energy indicators including S&P 500 market performance and
            Ember's Monthly Wind and Solar Capacity Data, all during the same timeframe from 2022-01-02 to 2024-12-24.</p>""", unsafe_allow_html=True)

    st.markdown("""<p style='text-align: left'>
            Our goal is to raise awareness about the global transition towards renewable energy, by delivering valuable information through text & audio, and reach more people, in more ways.</p>""", unsafe_allow_html=True)
            
    # Render the reusable footer
    render_footer()

    # --- Image Carousel ---
    st.markdown("---")
    
    # Get all image files from the home-carousel folder and subdirectories
    image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.webp', '*.avif']
    carousel_images = []
    
    for extension in image_extensions:
        # Search in main folder and subdirectories
        carousel_images.extend(glob.glob(f'website/images/home-carousel/**/{extension}', recursive=True))
    
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
    else:
        # Fallback to original image if no valid carousel images found
        st.image('website/images/home-carousel/renewables/ren_en_Image.png', width=200, use_container_width=True)


if __name__ == "__main__":
    main()
