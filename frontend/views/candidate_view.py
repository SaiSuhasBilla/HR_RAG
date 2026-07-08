import streamlit as st
import requests
import time

BACKEND_URL = "http://127.0.0.1:8000"
EXAM_DURATION_SECONDS = 600

def render():
    if "view_state" not in st.session_state: st.session_state.view_state = "login"

    if st.session_state.view_state == "login":
        st.title("💻 Technical Assessment Portal")
        st.info("Please enter your name exactly as it appeared on your resume file (e.g., 'Suhas_Resume' or 'John_Doe').")
        
        login_name = st.text_input("Candidate Identity Check:")
        
        if st.button("Fetch My Assessment"):
            if not login_name:
                st.warning("Please enter your name.")
                return
                
            with st.spinner("Locating your HR screening file..."):
                try:
                    res = requests.get(f"{BACKEND_URL}/get-candidate-test?name={login_name}").json()
                    
                    if res.get("status") == "not_found":
                        st.error("⚠️ No active assessment found. Make sure HR has processed your resume and you spelled your name correctly.")
                    elif res.get("status") == "rejected":
                        st.error("Thank you for your interest. Unfortunately, we are not hiring for that role currently or your profile did not meet the baseline threshold to move forward.")
                    else:
                        st.session_state.current_candidate_name = login_name
                        st.session_state.predicted_role = res["target_role"]
                        st.session_state.match_score = res["match_percentage"]
                        st.session_state.exam_data = res["exam"]
                        
                        st.success(f"Assessment found for {login_name}! Target Role: {res['target_role']}")
                        st.warning("⏱️ You will have exactly 10 minutes. Click below when ready.")
                        st.session_state.ready_to_start = True
                except Exception as e:
                    st.error(f"Backend connection error: {e}")
                    
        if st.session_state.get("ready_to_start"):
            if st.button("Start Exam Now", type="primary"):
                st.session_state.start_time = time.time()
                st.session_state.view_state = "exam"
                st.rerun()

    elif st.session_state.view_state == "exam":
        st.title(f"Technical Interview: {st.session_state.predicted_role}")
        
        elapsed = time.time() - st.session_state.start_time
        time_left = EXAM_DURATION_SECONDS - elapsed
        
        if time_left <= 0:
            st.error("⏳ Time is up! Processing your submission automatically...")
            total_score = 0
            with st.spinner("Grading saved answers..."):
                for idx, qa in enumerate(st.session_state.exam_data):
                    cand_ans = st.session_state.get(f"ans_{idx}", "")
                    try:
                        res = requests.post(f"{BACKEND_URL}/grade-answer", json={
                            "candidate_answer": cand_ans, "golden_answer": qa['a']
                        }).json()
                        total_score += res.get("score", 0.0)
                    except:
                        pass
                final_avg = total_score / len(st.session_state.exam_data) if st.session_state.exam_data else 0.0
                try:
                    requests.post(f"{BACKEND_URL}/submit-leaderboard", json={
                        "candidate_name": st.session_state.current_candidate_name,
                        "predicted_role": st.session_state.predicted_role,
                        "resume_score": st.session_state.match_score,
                        "interview_score": final_avg
                    })
                except: pass
                st.session_state.final_score = final_avg
                st.session_state.view_state = "results"
                st.rerun()
                
        mins, secs = divmod(int(time_left), 60)
        st.warning(f"⏱️ **Time Remaining:** {mins:02d}:{secs:02d}")
        st.progress(max(0.0, min(1.0, time_left / EXAM_DURATION_SECONDS)))
        st.divider()
        
        answers = []
        for idx, qa in enumerate(st.session_state.exam_data):
            st.markdown(f"### Q{idx+1} (`{qa['topic']}`)")
            st.markdown(f"**{qa['q']}**")
            ans = st.text_area("Your Answer:", key=f"ans_{idx}", height=140, placeholder="Type your technical solution here...")
            answers.append({"golden": qa['a'], "cand": ans})
            st.write("")
            
        if st.button("Submit Assessment", type="primary"):
            with st.spinner("Grading answers via local AI models..."):
                total_score = 0
                for pair in answers:
                    try:
                        grade = requests.post(f"{BACKEND_URL}/grade-answer", json={
                            "candidate_answer": pair["cand"], "golden_answer": pair["golden"]
                        }).json()
                        total_score += grade.get("score", 0.0)
                    except: pass
                        
                final_avg = total_score / len(answers) if answers else 0.0
                try:
                    requests.post(f"{BACKEND_URL}/submit-leaderboard", json={
                        "candidate_name": st.session_state.current_candidate_name,
                        "predicted_role": st.session_state.predicted_role,
                        "resume_score": st.session_state.match_score,
                        "interview_score": final_avg
                    })
                except: pass
                
                st.session_state.final_score = final_avg
                st.session_state.view_state = "results"
                st.rerun()

    elif st.session_state.view_state == "results":
        st.title("🏆 Assessment Complete")
        st.metric(label="Final AI Semantic Score", value=f"{st.session_state.final_score:.1f}%")
        
        if st.session_state.final_score >= 70.0:
            st.success("✅ **Passed!** You demonstrated excellent technical core competency.")
            st.balloons()
        else:
            st.error("❌ **Action Required:** Your evaluation score fell under the required 70% threshold.")
            
        st.divider()
        if st.button("Return to Log In Screen"):
            st.session_state.user_role = None
            st.session_state.view_state = "login"
            
            
            candidate_keys = ['current_candidate_name', 'predicted_role', 'match_score', 'exam_data', 'ready_to_start', 'start_time', 'final_score']
            for key in candidate_keys:
                if key in st.session_state:
                    del st.session_state[key]
                    
            st.rerun()