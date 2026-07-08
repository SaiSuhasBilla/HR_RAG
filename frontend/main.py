import streamlit as st
from views import login_view, hr_view, candidate_view
from utils.theme import apply_custom_theme
st.set_page_config(page_title="AI HR Platform", layout="wide")

apply_custom_theme()

if 'user_role' not in st.session_state: st.session_state.user_role = None
if 'view_state' not in st.session_state: st.session_state.view_state = "login"

st.sidebar.title("⚙️ Control Panel")
st.sidebar.markdown(f"**Current Role:** {st.session_state.user_role if st.session_state.user_role else 'None'}")

if st.session_state.user_role is not None:
    if st.sidebar.button("🚪 Logout / Switch Role", use_container_width=True):
        st.session_state.user_role = None
        st.session_state.view_state = "login"
        st.rerun()

st.sidebar.divider()
st.sidebar.info("🟢 System Online & Ready")


if st.session_state.user_role is None:
    login_view.render()
elif st.session_state.user_role == "HR":
    hr_view.render()
elif st.session_state.user_role == "Candidate":
    candidate_view.render()