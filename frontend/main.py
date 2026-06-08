import streamlit as st
from views import login_view, hr_view, candidate_view

st.set_page_config(page_title="AI HR Platform", layout="wide")

# --- Initialize Global Session State ---
if 'user_role' not in st.session_state: st.session_state.user_role = None
if 'predicted_role' not in st.session_state: st.session_state.predicted_role = None
if 'current_candidate_name' not in st.session_state: st.session_state.current_candidate_name = "Anonymous"
if 'exam_data' not in st.session_state: st.session_state.exam_data = []
if 'raw_resume_text' not in st.session_state: st.session_state.raw_resume_text = ""
if 'match_score' not in st.session_state: st.session_state.match_score = 0.0
if 'years_experience' not in st.session_state: st.session_state.years_experience = 0.0
if 'view_state' not in st.session_state: st.session_state.view_state = "login"

# --- Sidebar Navigation ---
st.sidebar.title("⚙️ Control Panel")
st.sidebar.markdown(f"**Current Role:** {st.session_state.user_role if st.session_state.user_role else 'None'}")

if st.session_state.user_role is not None:
    if st.sidebar.button("🚪 Logout / Switch Role", use_container_width=True):
        # FIXED: We only reset routing variables so the auto-generated test parameters stay alive in memory
        st.session_state.user_role = None
        st.session_state.view_state = "login"
        st.rerun()

st.sidebar.divider()
st.sidebar.info("System Status: Local Regex Engine Active")

# --- Router ---
if st.session_state.user_role is None:
    login_view.render()
elif st.session_state.user_role == "HR":
    hr_view.render()
elif st.session_state.user_role == "Candidate":
    candidate_view.render()