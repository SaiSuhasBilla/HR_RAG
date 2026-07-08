import streamlit as st
import requests
import pdfplumber
import pandas as pd

BACKEND_URL = "http://127.0.0.1:8000"

def extract_text_from_pdf(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            if extracted := page.extract_text(): text += extracted + "\n"
    return text

def render():
    st.title("HR Recruiter Dashboard")
    tab1, tab2 = st.tabs(["📄 Batch Resume Screener & RAG", "🏆 Leaderboard"])
    
    with tab1:
        st.subheader("1. Setup Target Role & Upload Resumes")
        
        try:
            roles = requests.get(f"{BACKEND_URL}/get-all-roles").json()
        except:
            roles = ["General Technical"]
            
        selected_role = st.selectbox("Select the Job Role you are hiring for:", roles)
        uploaded_files = st.file_uploader("Upload Candidate PDFs (Batch Upload)", type=['pdf'], accept_multiple_files=True)
        
        if uploaded_files and st.button("Process Batch Shortlist", type="primary"):
            with st.spinner(f"Screening {len(uploaded_files)} candidates against '{selected_role}'..."):
                payload_resumes = []
                for file in uploaded_files:
                    candidate_name = file.name.replace(".pdf", "").strip()
                    extracted_text = extract_text_from_pdf(file)
                    payload_resumes.append({"candidate_name": candidate_name, "raw_text": extracted_text})
                
                try:
                    requests.post(f"{BACKEND_URL}/screen-resumes-batch", json={
                        "target_role": selected_role,
                        "resumes": payload_resumes
                    })
                    st.success("Batch screening complete! Data safely saved to server.")
                except Exception as e:
                    st.error(f"Backend connection failed: {e}")

        
        try:
            active_batch = requests.get(f"{BACKEND_URL}/get-active-batch").json()
        except Exception:
            active_batch = []

        if active_batch:
            st.divider()
            
            shortlisted = [c for c in active_batch if c["status"] == "Shortlisted"]
            rejected = [c for c in active_batch if c["status"] == "Rejected"]
            
            st.subheader("2. Candidate Shortlist Matrix (>= 50% Match)")
            if shortlisted:
                df_short = pd.DataFrame(shortlisted).rename(columns={
                    "candidate_name": "Candidate", "match_percentage": "Match Score %", "years_experience": "Experience (Yrs)"
                })
                st.dataframe(df_short[["Candidate", "Match Score %", "Experience (Yrs)"]], use_container_width=True, hide_index=True)
            else:
                st.warning("No candidates met the 50% threshold for this role.")
                
            if rejected:
                with st.expander(f"View Rejected Candidates (< 50% Match) - {len(rejected)} found"):
                    df_rej = pd.DataFrame(rejected).rename(columns={
                        "candidate_name": "Candidate", "match_percentage": "Match Score %"
                    })
                    st.dataframe(df_rej[["Candidate", "Match Score %"]], use_container_width=True, hide_index=True)
            
            st.divider()
            st.subheader("3. Interact With Candidate Resume")
            if shortlisted:
                candidate_names = [r["candidate_name"] for r in shortlisted]
                chat_target = st.selectbox("Select a shortlisted candidate to review:", candidate_names)
                
                selected_data = next(c for c in shortlisted if c["candidate_name"] == chat_target)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Experience", f"{selected_data['years_experience']} Years")
                with col2:
                    missing_str = ", ".join(selected_data['missing_skills']).title() if selected_data['missing_skills'] else "None"
                    st.warning(f"**Missing Skills:** {missing_str}")
                
                recruiter_q = st.text_input(f"Ask a question specifically about {chat_target}'s experience:")
                if st.button("Query Candidate Document") and recruiter_q:
                    with st.spinner("Searching candidate file..."):
                        rag_res = requests.post(f"{BACKEND_URL}/chat-resume", json={
                            "candidate_name": chat_target, "question": recruiter_q
                        }).json()
                        st.info(f"**AI Answer:** {rag_res['answer']}")
            else:
                st.info("No shortlisted candidates available for RAG query.")

    with tab2:
        st.subheader("🏆 Session Leaderboard")
        try:
            lb_data = requests.get(f"{BACKEND_URL}/get-leaderboard").json()
            if lb_data:
                df = pd.DataFrame(lb_data).sort_values(by="Interview Score %", ascending=False)
                df.insert(0, "Rank", range(1, len(df) + 1))
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No candidates have completed exams in this active session.")
        except Exception:
            st.error("Failed to load leaderboard data.")