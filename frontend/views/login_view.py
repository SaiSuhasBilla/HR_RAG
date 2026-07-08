import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()
HR_USER = os.getenv("HR_USERNAME", "admin")
HR_PASS = os.getenv("HR_PASSWORD", "admin123") 

def render():
    st.title("🔒 Welcome to the AI HR Platform")
    st.markdown("### Please select your role to continue:")
    st.write("---")
    
    if "show_hr_login" not in st.session_state:
        st.session_state.show_hr_login = False
        
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(" 👔 **For HR Professionals**\n\nBatch screen candidates, rank resumes, and query files.")
        if st.button("Log in as HR Recruiter", use_container_width=True):
            st.session_state.show_hr_login = True
            
    with col2:
        st.success(" 💻 **For Job Applicants**\n\nLog in with your name to take your HR-assigned assessment.")
        if st.button("Log in as Candidate", use_container_width=True):
            st.session_state.show_hr_login = False 
            st.session_state.user_role = "Candidate"
            st.session_state.view_state = "login"
            st.rerun()

    if st.session_state.show_hr_login:
        st.write("---")
        st.subheader("🔑 HR Security Gateway")
        
        with st.form("hr_login_form"):
            username = st.text_input("Username:", placeholder="Enter HR username")
            password = st.text_input("Password:", type="password", placeholder="Enter secure password")
            submit_login = st.form_submit_button("Verify Credentials", type="primary", use_container_width=True)
            
            if submit_login:
                if username == HR_USER and password == HR_PASS:
                    st.success("Access Granted! Loading secure recruiter workspace...")
                    st.session_state.user_role = "HR"
                    st.session_state.show_hr_login = False
                    st.rerun()
                else:
                    st.error("❌ Invalid Username or Password. Access Denied.")