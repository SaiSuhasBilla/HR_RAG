import streamlit as st
import requests
import time

BACKEND_URL = "http://127.0.0.1:8000"
EXAM_DURATION_SECONDS = 600  # 10 minutes

def render():
    # --- 1. PREREQUISITE INITIALIZATION CHECKS ---
    if not st.session_state.get("predicted_role") or not st.session_state.get("exam_data"):
        st.title("💻 Technical Assessment Portal")
        st.warning("⚠️ No active assessment found. Ask your HR Recruiter to generate your test.")
        return

    if "view_state" not in st.session_state:
        st.session_state.view_state = "login"

    # --- 2. STATE: LOGIN / INSTRUCTIONS GATE ---
    if st.session_state.view_state == "login":
        st.title(f"Welcome, {st.session_state.get('current_candidate_name', 'Candidate')}!")
        st.info(f"Your assessment for **{st.session_state.predicted_role}** is ready.")
        st.warning("⏱️ **Important:** You will have exactly 10 minutes to complete this exam. Leaving or refreshing the page will reset your progress.")
        
        if st.button("Start Exam Now", type="primary"):
            st.session_state.start_time = time.time()
            st.session_state.view_state = "exam"
            st.rerun()

    # --- 3. STATE: ACTIVE ASSESSMENT WITH LIVE TIMER ---
    elif st.session_state.view_state == "exam":
        st.title(f"Technical Interview: {st.session_state.predicted_role}")
        
        # Calculate dynamic timeline drift
        elapsed = time.time() - st.session_state.start_time
        time_left = EXAM_DURATION_SECONDS - elapsed
        
        # CRITICAL REFACTOR: Graceful Auto-Timeout Execution Wrapper
        if time_left <= 0:
            st.error("⏳ Time is up! Processing your submission automatically...")
            
            total_score = 0
            with st.spinner("Grading saved answers via local models..."):
                for idx, qa in enumerate(st.session_state.exam_data):
                    # Pull values directly from Streamlit's state tree keys
                    cand_ans = st.session_state.get(f"ans_{idx}", "")
                    try:
                        res = requests.post(f"{BACKEND_URL}/grade-answer", json={
                            "candidate_answer": cand_ans, "golden_answer": qa['a']
                        }).json()
                        total_score += res.get("score", 0.0)
                    except Exception:
                        total_score += 0.0
                        
                final_avg = total_score / len(st.session_state.exam_data) if st.session_state.exam_data else 0.0
                
                # Push incomplete progress values straight to backend storage 
                try:
                    requests.post(f"{BACKEND_URL}/submit-leaderboard", json={
                        "candidate_name": st.session_state.get('current_candidate_name', 'Anonymous'),
                        "predicted_role": st.session_state.predicted_role,
                        "resume_score": st.session_state.get('match_score', 0.0),
                        "interview_score": final_avg
                    })
                except Exception:
                    pass
                
                st.session_state.final_score = final_avg
                st.session_state.view_state = "results"
                st.rerun()
                
        # Render Timer Metrics Bar
        mins, secs = divmod(int(time_left), 60)
        st.warning(f"⏱️ **Time Remaining:** {mins:02d}:{secs:02d}")
        st.progress(max(0.0, min(1.0, time_left / EXAM_DURATION_SECONDS)))
        st.divider()
        
        # Generate Interactive Questionnaire Elements
        answers = []
        for idx, qa in enumerate(st.session_state.exam_data):
            st.markdown(f"### Q{idx+1} (`{qa['topic']}`)")
            st.markdown(f"**{qa['q']}**")
            ans = st.text_area("Your Answer:", key=f"ans_{idx}", height=140, placeholder="Type your technical solution here...")
            answers.append({"golden": qa['a'], "cand": ans})
            st.write("") # Layout spacer
            
        # Standard Manual Form Submission
        if st.button("Submit Assessment", type="primary"):
            with st.spinner("Grading answers via local AI models..."):
                total_score = 0
                for pair in answers:
                    try:
                        grade = requests.post(f"{BACKEND_URL}/grade-answer", json={
                            "candidate_answer": pair["cand"], "golden_answer": pair["golden"]
                        }).json()
                        total_score += grade.get("score", 0.0)
                    except Exception:
                        total_score += 0.0
                        
                final_avg = total_score / len(answers) if answers else 0.0
                
                # Push score record matrix up to global leaderboard
                try:
                    requests.post(f"{BACKEND_URL}/submit-leaderboard", json={
                        "candidate_name": st.session_state.get('current_candidate_name', 'Anonymous'),
                        "predicted_role": st.session_state.predicted_role,
                        "resume_score": st.session_state.get('match_score', 0.0),
                        "interview_score": final_avg
                    })
                except Exception:
                    st.error("Warning: Could not save final results to leaderboard file storage.")
                
                st.session_state.final_score = final_avg
                st.session_state.view_state = "results"
                st.rerun()

    # --- 4. STATE: SCORE EVALUATION REPORT CARD ---
    elif st.session_state.view_state == "results":
        st.title("🏆 Assessment Complete")
        
        # Centered visual scoring card
        st.metric(label="Final AI Semantic Score", value=f"{st.session_state.final_score:.1f}%")
        
        if st.session_state.final_score >= 70.0:
            st.success("✅ **Passed!** You demonstrated excellent technical core competency and keyword alignment.")
            st.balloons()
        else:
            st.error("❌ **Action Required:** Your evaluation score fell under the required 70% baseline threshold. Review core operational concepts for this role.")
            
        st.divider()
        if st.button("Return to Log In Screen"):
            # Clear current session tokens smoothly so another candidate can log in immediately
            st.session_state.clear()
            st.rerun()