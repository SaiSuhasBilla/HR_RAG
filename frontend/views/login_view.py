import streamlit as st

def render():
    st.title("Welcome to the AI HR Platform")
    st.markdown("### Please select your role to continue:")
    st.write("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("👔 **For HR Professionals**\n\nUpload resumes, screen candidates, and chat with documents.")
        if st.button("Log in as HR Recruiter", use_container_width=True):
            st.session_state.user_role = "HR"
            st.rerun()
            
    with col2:
        st.success("💻 **For Job Applicants**\n\nTake your dynamically generated technical assessment.")
        if st.button("Log in as Candidate", use_container_width=True):
            st.session_state.user_role = "Candidate"
            st.rerun()