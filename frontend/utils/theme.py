import streamlit as st

def apply_custom_theme():
    st.markdown(
        """
        <style>
        /* 1. Global App Background */
        .stApp {
            /* Swap this URL with any of the options above */
            background-image: url("https://images.unsplash.com/photo-1639322537228-f710d846310a?q=80&w=2000&auto=format&fit=crop");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }

        /* 2. Main Content Container - bright enough to read text clearly */
        .main .block-container {
            background: rgba(255, 255, 255, 0.90);
            padding: 3rem 4rem;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            margin-top: 2rem;
            margin-bottom: 2rem;
        }

        /* Dark mode compatibility override for the main container */
        @media (prefers-color-scheme: dark) {
            .main .block-container {
                background: rgba(22, 24, 29, 0.92);
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
            }
        }

        /* 3. Darker, Smoked-Glass Sidebar */
        [data-testid="stSidebar"] {
            /* Dark semi-transparent background instead of bright white */
            background-color: rgba(15, 20, 25, 0.35) !important; 
            /* Heavy blur creates the frosted glass look */
            backdrop-filter: blur(15px) !important;
            -webkit-backdrop-filter: blur(15px) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* sidebar text stays readable against the new dark glass */
        [data-testid="stSidebar"] * {
            color: white !important; 
        }

        /* 4. Stylize buttons */
        .stButton>button {
            border-radius: 6px !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            transition: all 0.2s ease;
        }
        </style>
        """,
        unsafe_allow_html=True
    )