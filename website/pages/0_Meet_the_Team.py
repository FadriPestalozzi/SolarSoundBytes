import streamlit as st
from PIL import Image
import sys
import os
import base64
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared_components import get_emoji_title, render_footer

def get_base64_of_bin_file(bin_file):
    """Convert binary file to base64 string"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def render_about_us():
    # Load GitHub and LinkedIn logos as base64
    github_logo_base64 = get_base64_of_bin_file('website/images/github_logo.png')
    linkedin_logo_base64 = get_base64_of_bin_file('website/images/linkedin_logo.png')
    
    # Custom CSS for better alignment and styling
    st.markdown("""
    <style>
        .team-title {
            text-align: center;
            font-size: 3rem;
            margin-bottom: 2rem;
            color: #ffffff;
        }

        .team-member {
            text-align: center;
            padding: 20px;
            height: 100%;
        }

        .team-member h3 {
            color: #ffffff;
            margin-bottom: 1rem;
            font-size: 1.5rem;
        }

        .team-image {
            border-radius: 10px;
            margin-bottom: 1rem;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        .social-links {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 1rem;
        }

        .social-link {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 8px 12px;
            background-color: #f0f2f6;
            border-radius: 20px;
            text-decoration: none;
            color: #333;
            transition: background-color 0.3s;
        }

        .social-link:hover {
            background-color: #e1e5e9;
        }

        .profile-description {
            text-align: justify;
            line-height: 1.6;
            margin: 1rem 0;
        }
    </style>
    """, unsafe_allow_html=True)

    # Add CSS to center images and style buttons
    st.markdown("""
    <style>
    .team-name {
        height: 48px;   /* Adjust as needed to fit the longest name */
        display: flex;
        align-items: flex-end; /* Align text to bottom of the area for nice look */
        justify-content: center;
        font-size: 1.5rem;
        font-weight: bold;
        color: #fff;
        margin-bottom: 1rem;
    }
    
    /* Removed old stLinkButton styling - now using custom buttons for both LinkedIn and GitHub */
    
    /* Custom GitHub button styling to match LinkedIn buttons exactly */
    .github-button {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 4px 8px !important;
        background-color: transparent !important;
        color: inherit !important;
        text-decoration: none !important;
        border-radius: 0.5rem !important;
        font-size: 14px !important;
        font-weight: 400 !important;
        font-family: "Source Sans Pro", sans-serif !important;
        border: 1px solid rgba(49, 51, 63, 0.2) !important;
        cursor: pointer !important;
        transition: border-color 0.2s, color 0.2s !important;
        width: 100% !important;
        box-sizing: border-box !important;
        white-space: nowrap !important;
        text-overflow: ellipsis !important;
        text-align: center !important;
        height: 38px !important;
        line-height: 38px !important;
        vertical-align: middle !important;
    }
    
    .github-button:hover {
        border-color: #ff4b4b !important;
        color: #ff4b4b !important;
        text-decoration: none !important;
    }
    
    .github-logo {
        width: 16px !important;
        height: 16px !important;
        margin-right: 6px !important;
    }
    
    /* Force same exact styling for GitHub button text */
    .github-button span, .github-button {
        font-family: "Source Sans Pro", sans-serif !important;
        font-size: 14px !important;
        font-weight: 400 !important;
        letter-spacing: 0px !important;
        line-height: 1.6 !important;
    }
    
    /* Custom LinkedIn button styling to match GitHub buttons exactly */
    .linkedin-button {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 4px 8px !important;
        background-color: transparent !important;
        color: inherit !important;
        text-decoration: none !important;
        border-radius: 0.5rem !important;
        font-size: 14px !important;
        font-weight: 400 !important;
        font-family: "Source Sans Pro", sans-serif !important;
        border: 1px solid rgba(49, 51, 63, 0.2) !important;
        cursor: pointer !important;
        transition: border-color 0.2s, color 0.2s !important;
        width: 100% !important;
        box-sizing: border-box !important;
        white-space: nowrap !important;
        text-overflow: ellipsis !important;
        text-align: center !important;
        height: 38px !important;
        line-height: 38px !important;
        vertical-align: middle !important;
    }
    
    .linkedin-button:hover {
        border-color: #ff4b4b !important;
        color: #ff4b4b !important;
        text-decoration: none !important;
    }
    
    .linkedin-logo {
        width: 16px !important;
        height: 16px !important;
        margin-right: 6px !important;
    }
    
    /* Align footer section headers */
    .stats-section {
        text-align: left !important;
    }
    
    .stats-section h3 {
        text-align: left !important;
        font-size: 1.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    .stats-section .emoji {
        font-size: 2rem !important;
    }
    
    /* Justify text in team member descriptions */
    .stMarkdown p {
        text-align: justify !important;
        text-justify: inter-word !important;
        hyphens: auto !important;
        line-height: 1.6 !important;
        margin-bottom: 1rem !important;
    }
    
    /* Ensure consistent column width */
    .element-container {
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)


    # Centered title
    st.markdown(f'<h1 class="team-title">{get_emoji_title(include_team=True)}</h1>', unsafe_allow_html=True)

    # Create 3 equal columns with proper spacing
    col1, col2, col3 = st.columns(3, gap="medium")

    #FADRI PESTALOZZI
    with col1:
        st.markdown('<div class="team-name">Fadri Pestalozzi</div>', unsafe_allow_html=True)
        # st.subheader("Fadri Pestalozzi")
        image = Image.open('website/images/Fadri.jpeg').resize((320, 320))
        st.image(image)
        st.write("Mechanical engineer turned software developer proficient in Python, SQL, and Odoo. After building a strong backend foundation, he's currently diving into ML/AI through community‑driven bootcamps and open-source events. Motivated by collaborative impact and continuous upskilling.")
        # link buttons
        col_linkedin, col_github = st.columns(2)
        with col_linkedin:
            st.markdown(
                f'<a href="https://www.linkedin.com/in/fadri-pestalozzi/" target="_blank" class="linkedin-button">'
                f'<img src="data:image/png;base64,{linkedin_logo_base64}" class="linkedin-logo" alt="LinkedIn">LinkedIn</a>',
                unsafe_allow_html=True
            )
        with col_github:
            st.markdown(
                f'<a href="https://github.com/FadriPestalozzi" target="_blank" class="github-button">'
                f'<img src="data:image/png;base64,{github_logo_base64}" class="github-logo" alt="GitHub">GitHub</a>',
                unsafe_allow_html=True
            )


    # STEFFEN LAUTERBACH
    with col2:
        st.markdown('<div class="team-name">Steffen Lauterbach</div>', unsafe_allow_html=True)
        # st.subheader("Steffen Lauterbach")
        image = Image.open('website/images/SteffenLauterbach.png').resize((320, 320))
        st.image(image)
        st.write("Renewable energy engineer and former research associate with deep experience in designing and optimizing clean energy systems. Passionate about bridging technical innovation with real-world impact. Committed to driving the next wave of green energy solutions.")
        # link buttons
        col_linkedin, col_github = st.columns(2)
        with col_linkedin:
            st.markdown(
                f'<a href="https://www.linkedin.com/in/92-steffen-lauterbach/" target="_blank" class="linkedin-button">'
                f'<img src="data:image/png;base64,{linkedin_logo_base64}" class="linkedin-logo" alt="LinkedIn">LinkedIn</a>',
                unsafe_allow_html=True
            )
        with col_github:
            st.markdown(
                f'<a href="https://github.com/SL14-SL" target="_blank" class="github-button">'
                f'<img src="data:image/png;base64,{github_logo_base64}" class="github-logo" alt="GitHub">GitHub</a>',
                unsafe_allow_html=True
            )

    # ENRIQUE FLORES ROLDÁN
    with col3:
        st.markdown('<div class="team-name">Enrique Flores Roldán</div>', unsafe_allow_html=True)
        # st.subheader("Enrique Flores Roldán")
        image = Image.open('website/images/Enrique.jpeg')
        width, height = image.size
        size = min(width, height)  # Use the smaller dimension
        left = (width - size) // 2
        top = (height - size) // 2
        right = left + size
        bottom = top + size
        image = image.crop((left, top, right, bottom))
        image = image.resize((320, 320), Image.Resampling.LANCZOS)
        st.image(image)
        st.write("Video producer with 12 years of experience crafting visual storytelling across TV, advertising, and corporate media. Now pursuing a career shift into ML and AI to fuse creativity with cutting‑edge technology. Eager to apply narrative expertise in building intelligent, engaging solutions.")
        # link buttons
        col_linkedin, col_github = st.columns(2)
        with col_linkedin:
            st.markdown(
                f'<a href="https://www.linkedin.com/in/enriqfr5/" target="_blank" class="linkedin-button">'
                f'<img src="data:image/png;base64,{linkedin_logo_base64}" class="linkedin-logo" alt="LinkedIn">LinkedIn</a>',
                unsafe_allow_html=True
            )
        with col_github:
            st.markdown(
                f'<a href="https://github.com/EFRdev" target="_blank" class="github-button">'
                f'<img src="data:image/png;base64,{github_logo_base64}" class="github-logo" alt="GitHub">GitHub</a>',
                unsafe_allow_html=True
            )


def main():
    """Main function to run the page"""
    st.set_page_config(page_title="About Us @ ☀️🔊🍔", page_icon="👥", layout="wide")
    render_about_us()
    render_footer()

if __name__ == "__main__":
    main()
