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
    st.title("👔 HR Recruiter Dashboard")
    tab1, tab2 = st.tabs(["📄 Resume Screener & RAG", "🏆 Leaderboard"])
    
    with tab1:
        col1, col2 = st.columns([1, 1])
        with col1:
            candidate_name = st.text_input("Candidate Name:", placeholder="e.g. John Doe")
            resume_pdf = st.file_uploader("Upload Candidate PDF", type=['pdf'])
            
            if resume_pdf and st.button("Process Candidate Profile", type="primary"):
                with st.spinner("Processing candidate profile..."):
                    st.session_state.current_candidate_name = candidate_name if candidate_name else "Anonymous"
                    extracted_text = extract_text_from_pdf(resume_pdf)
                    st.session_state.raw_resume_text = extracted_text
                    
                    try:
                        res = requests.post(f"{BACKEND_URL}/screen-resume", json={"raw_text": extracted_text}).json()
                        
                        if "detail" in res:
                            st.error(f"Backend Error: {res['detail']}")
                        else:
                            st.session_state.predicted_role = res["predicted_role"]
                            st.session_state.match_score = res["match_percentage"]
                            st.session_state.missing_skills = res["missing_skills"]
                            st.session_state.years_experience = res.get("years_experience", 0.0)
                            
                            exam_res = requests.get(f"{BACKEND_URL}/get-questions?role={res['predicted_role']}").json()
                            st.session_state.exam_data = exam_res
                            
                    except Exception as e:
                        st.error(f"Backend connection failed: {e}")

        with col2:
            if st.session_state.predicted_role:
                st.subheader("📊 Screening Report")
                st.metric("Predicted Role", st.session_state.predicted_role)
                st.metric("Total Match Score", f"{st.session_state.match_score:.1f}%")
                st.metric("Detected Experience", f"{st.session_state.get('years_experience', 0.0)} Years")
                
                if st.session_state.missing_skills:
                    st.warning(f"**⚠️ Missing Skills:** {', '.join(st.session_state.missing_skills).title()}")
                else:
                    st.success("**✅ All core skills matched!**")

        if st.session_state.predicted_role:
            st.divider()
            st.subheader("🤖 RAG: Ask the Resume")
            recruiter_q = st.text_input("Ask a factual question about the candidate's experience:")
            if st.button("Query Document") and recruiter_q:
                with st.spinner("Executing Local Semantic Search..."):
                    rag_res = requests.post(f"{BACKEND_URL}/chat-resume", json={
                        "raw_text": st.session_state.raw_resume_text, "question": recruiter_q
                    }).json()
                    st.info(f"**AI Answer:** {rag_res['answer']}")

    with tab2:
        st.subheader("🏆 Candidate Leaderboard")
        try:
            lb_data = requests.get(f"{BACKEND_URL}/get-leaderboard").json()
            if lb_data:
                df = pd.DataFrame(lb_data).sort_values(by="Interview Score %", ascending=False)
                df.insert(0, "Rank", range(1, len(df) + 1))
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No candidates on the leaderboard yet.")
        except Exception:
            st.error("Failed to load leaderboard data.")