import os
import random
import json
import re
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer, util
from google import genai

from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

print("Loading Local Sentence Transformer...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

print("Configuring Gemini Client...")
client = genai.Client()

SKILL_ROLE_MATRIX: Dict[str, set] = {}
QUESTION_BANK: Dict[str, list] = {}
ALL_UNIQUE_SKILLS = set()

CANDIDATE_POOL: Dict[str, Dict[str, Any]] = {}
LEADERBOARD_DATA: List[Dict[str, Any]] = []

try:
    df = pd.read_csv("it_jobs_required_skills.csv")
    for _, row in df.iterrows():
        role = str(row['job_title']).strip()
        skills_raw = str(row['required_skills']) if not pd.isna(row['required_skills']) else ""
        parsed_skills = [s.strip().lower() for s in skills_raw.split('|') if s.strip()]
        SKILL_ROLE_MATRIX[role] = set(parsed_skills)
        ALL_UNIQUE_SKILLS.update(parsed_skills)
        
    with open("questions.json", "r") as f:
        QUESTION_BANK = json.load(f)
    print(f"✅ Datasets verified. Tracking {len(ALL_UNIQUE_SKILLS)} skills across {len(SKILL_ROLE_MATRIX)} positions.")
except Exception as e:
    print(f"❌ Initialization Error: {e}")

class SingleResumeInput(BaseModel):
    candidate_name: str
    raw_text: str

class BatchScreenRequest(BaseModel):
    target_role: str
    resumes: List[SingleResumeInput]

class MultiUserChatRequest(BaseModel):
    candidate_name: str
    question: str

class GradeRequest(BaseModel):
    candidate_answer: str
    golden_answer: str

class LeaderboardEntry(BaseModel):
    candidate_name: str
    predicted_role: str
    resume_score: float
    interview_score: float

@app.get("/get-all-roles")
def get_all_roles():
    return sorted(list(SKILL_ROLE_MATRIX.keys()))

@app.get("/get-active-batch")
def get_active_batch():
    """Allows the HR frontend to recover the shortlisted candidates directly from the server memory."""
    res = []
    for name, data in CANDIDATE_POOL.items():
        res.append({
            "candidate_name": name,
            "target_role": data["target_role"],
            "match_percentage": data["match_percentage"],
            "years_experience": data["years_experience"],
            "missing_skills": data["missing_skills"],
            "extracted_skills": data["extracted_skills"],
            "status": data["status"]
        })
    return sorted(res, key=lambda x: x["match_percentage"], reverse=True)

@app.post("/screen-resumes-batch")
def screen_resumes_batch(req: BatchScreenRequest):
    target_role = req.target_role
    if target_role not in SKILL_ROLE_MATRIX:
        raise HTTPException(status_code=404, detail=f"Job target '{target_role}' not registered.")
        
    required_skills = SKILL_ROLE_MATRIX[target_role]
    response_list = []

    for item in req.resumes:
        name = item.candidate_name.strip()
        text_lower = item.raw_text.lower()
        candidate_skills = set()

        for skill in ALL_UNIQUE_SKILLS:
            escaped_skill = re.escape(skill)
            pattern = rf"\b{escaped_skill}\b" if skill.isalnum() else rf"(?:^|\s|[^a-zA-Z0-9]){escaped_skill}(?:$|\s|[^a-zA-Z0-9])"
            if re.search(pattern, text_lower):
                candidate_skills.add(skill)

        years_exp = 0.0
        exp_pattern = r"(?:total\s+)?experience\s*:\s*([\d\.]+)|([\d\.]+)\s*[:+]?\s*(?:years?|yrs?)\s*(?:of\s+)?experience"
        matches = re.findall(exp_pattern, text_lower)
        for match in matches:
            num_str = match[0] if match[0] else match[1]
            if num_str:
                try:
                    years_exp = float(num_str)
                    break
                except ValueError:
                    continue

        if required_skills:
            matching_intersection = candidate_skills.intersection(required_skills)
            match_pct = (len(matching_intersection) / len(required_skills)) * 100
            missing = list(required_skills - candidate_skills)
        else:
            match_pct = 0.0
            missing = []

        if match_pct >= 50.0:
            status = "Shortlisted"
            skills_pool = list(required_skills) if required_skills else ["python", "sql", "git"]
            
            skill_buckets = {}
            for s in skills_pool:
                if s in QUESTION_BANK and QUESTION_BANK[s]:
                    skill_buckets[s] = [{"topic": s.upper(), "q": q["q"], "a": q["a"]} for q in QUESTION_BANK[s]]
            
            if not skill_buckets: 
                skill_buckets = {"GENERAL": [{"topic": "GENERAL", "q": "Explain your understanding of this tech domain.", "a": ""}]}
            
            custom_exam = []
            remaining_pool = []
            
            available_skills = list(skill_buckets.keys())
            random.shuffle(available_skills)
            
            for s in available_skills:
                if len(custom_exam) >= 10: break
                q_list = skill_buckets[s]
                chosen_q = random.choice(q_list)
                custom_exam.append(chosen_q)
                for q in q_list:
                    if q != chosen_q: remaining_pool.append(q)
                        
            deficit = 10 - len(custom_exam)
            if deficit > 0:
                if len(remaining_pool) >= deficit:
                    custom_exam.extend(random.sample(remaining_pool, deficit))
                else:
                    custom_exam.extend(remaining_pool)
                    while len(custom_exam) < 10 and custom_exam:
                        custom_exam.append(random.choice(custom_exam))
                        
            random.shuffle(custom_exam)
            
        else:
            status = "Rejected"
            custom_exam = [] 

        CANDIDATE_POOL[name] = {
            "raw_text": item.raw_text,
            "target_role": target_role,
            "match_percentage": round(match_pct, 2),
            "extracted_skills": list(candidate_skills),
            "missing_skills": missing,
            "years_experience": years_exp,
            "exam_data": custom_exam,
            "status": status
        }

        response_list.append({
            "candidate_name": name,
            "match_percentage": round(match_pct, 2),
            "years_experience": years_exp,
            "missing_skills": missing,
            "extracted_skills": list(candidate_skills),
            "status": status
        })

    return sorted(response_list, key=lambda x: x["match_percentage"], reverse=True)

@app.post("/chat-resume")
def chat_resume(req: MultiUserChatRequest):
    name = req.candidate_name.strip()
    if name not in CANDIDATE_POOL:
        return {"answer": f"No active resume profile loaded in server memory for candidate: '{name}'"}

    raw_text = CANDIDATE_POOL[name]["raw_text"]
    chunk_size, step = 1500, 1200
    chunks = []
    text_len = len(raw_text)
    
    if text_len <= chunk_size:
        chunks = [raw_text]
    else:
        for i in range(0, text_len, step):
            chunk = raw_text[i:i+chunk_size]
            if chunk.strip():
                chunks.append(chunk)

    if not chunks: 
        return {"answer": f"Candidate file parsed completely empty."}

    chunk_embeddings = embedding_model.encode(chunks, convert_to_tensor=True)
    query_embedding = embedding_model.encode(req.question, convert_to_tensor=True)
    
    hits = util.semantic_search(query_embedding, chunk_embeddings, top_k=3)[0]
    top_chunks = [chunks[hit['corpus_id']] for hit in hits]
    context = "\n... \n".join(top_chunks)
    
    prompt = f"""
    You are an intelligent HR assistant profiling candidate '{name}' for '{CANDIDATE_POOL[name]['target_role']}'.
    Synthesize and write natural summaries rather than raw copy-pasting. Stay 100% truthful to the context.

    Context:
    {context}

    Question: {req.question}
    """
    try:
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        return {"answer": response.text}
    except Exception as e:
        return {"answer": f"Chat processing failed due to API status connection issues: {e}"}

@app.get("/get-candidate-test")
def get_candidate_test(name: str = Query(...)):
    candidate_key = name.strip()
    if candidate_key in CANDIDATE_POOL:
        cand_data = CANDIDATE_POOL[candidate_key]
        if cand_data["status"] == "Shortlisted":
            return {
                "status": "found",
                "target_role": cand_data["target_role"],
                "match_percentage": cand_data["match_percentage"],
                "exam": cand_data["exam_data"]
            }
        else:
            return {"status": "rejected"}
    return {"status": "not_found"}

@app.post("/grade-answer")
def grade_answer(req: GradeRequest):
    if len(req.candidate_answer.split()) < 3: return {"score": 0.0, "feedback": "Answer too short to analyze."}
    cand_vec = embedding_model.encode(req.candidate_answer, convert_to_tensor=True)
    gold_vec = embedding_model.encode(req.golden_answer, convert_to_tensor=True)
    similarity = util.cos_sim(cand_vec, gold_vec).item()
    return {"score": max(0, min(100, round(similarity * 100)))}

@app.post("/submit-leaderboard")
def submit_leaderboard(entry: LeaderboardEntry):
    LEADERBOARD_DATA.append({
        "Candidate Name": entry.candidate_name, 
        "Predicted Role": entry.predicted_role, 
        "Resume Match %": round(entry.resume_score, 1), 
        "Interview Score %": round(entry.interview_score, 1)
    })
    return {"status": "success"}

@app.get("/get-leaderboard")
def get_leaderboard():
    return LEADERBOARD_DATA