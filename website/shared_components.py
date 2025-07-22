"""
Shared UI components for the SolarSoundBytes website
"""
import streamlit as st
import base64

def get_emoji_title(include_team=False):
    """
    Returns the consistent emoji title for SolarSoundBytes
    
    Args:
        include_team (bool): Whether to include "Team" at the end
    
    Returns:
        str: The emoji title string
    """
    base_title = "☀️Solar🔊Sound🍔Bytes"
    if include_team:
        return f"{base_title}👥Team"
    return base_title

def render_emoji_title_header(include_team=False, size="h1", center=True):
    """
    Renders the emoji title as an HTML header
    
    Args:
        include_team (bool): Whether to include "Team" at the end
        size (str): HTML header size (h1, h2, h3, etc.)
        center (bool): Whether to center the title
    
    Returns:
        str: HTML string for the title
    """
    title = get_emoji_title(include_team)
    alignment = "text-align: center" if center else "text-align: left"
    
    return f'<{size} style="{alignment}">{title}</{size}>'

def get_emoji_link_text():
    """
    Returns the emoji title formatted for use in links
    
    Returns:
        str: The emoji title for links
    """
    return get_emoji_title(include_team=True)

def get_base64_image(image_path):
    """
    Convert image to base64 string to preserve quality and prevent format conversion
    
    Args:
        image_path (str): Path to the image file
    
    Returns:
        str: Base64 encoded image string
    """
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        st.error(f"Image not found: {image_path}")
        return ""

def render_footer():
    """
    Renders the consistent footer for all pages with Le Wagon branding and team info
    """
    # footer = two columns for icon and text
    st.markdown("---")
    img_col, text_col = st.columns([1, 10])   # width ratio
    
    with img_col:
        # Use base64 encoding to preserve PNG quality and prevent JPG conversion
        img_base64 = get_base64_image('website/images/LeWagonIcon.png')
        if img_base64:
            st.markdown(
                f'<img src="data:image/png;base64,{img_base64}" width="70" style="display: block; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">',
                unsafe_allow_html=True
            )
        else:
            # Fallback to st.image if base64 fails
            st.image('website/images/LeWagonIcon.png', width=70)
    
    with text_col:
        st.markdown(f"""
            <div style="margin-top: 0px;">
                <div style="font-size: 16px; margin-bottom: 2px; white-space: nowrap;">🚁 Lift-off as final project of our <a href="https://www.lewagon.com/barcelona/data-science-course" target="_blank">🥾 Le Wagon  Data Science Bootcamp</a> batch #2012 in 🏖️ Barcelona  </div>
                <div style="font-size: 16px; margin-bottom: 2px; white-space: nowrap;">🫀 Created with love by the <a href="/Meet_the_Team">{get_emoji_link_text()}</a> </div>
                <div style="font-size: 16px; color: #666; white-space: nowrap;">💪 Please <a href="https://github.com/FadriPestalozzi/SolarSoundBytes/discussions/categories/ideas" target="_blank">🧠 tell us what you think</a> so we can reach for the 🚀 stars together</div>
            </div>
        """, unsafe_allow_html=True) 