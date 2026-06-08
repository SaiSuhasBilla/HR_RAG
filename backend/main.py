import os
import random
import json
import re
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from sentence_transformers import SentenceTransformer, util
from google import genai

app = FastAPI()

# --- 1. INITIALIZE LOCAL MODELS & SERVICES ---
print("Loading Local Sentence Transformer...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

print("Configuring Gemini Client (Used only for conversational RAG)...")
client = genai.Client()

# --- 2. LOAD DATASETS ON STARTUP ---
SKILL_ROLE_MATRIX = {}
QUESTION_BANK = {}
ALL_UNIQUE_SKILLS = set()
LEADERBOARD_FILE = "leaderboard.csv"

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
    print(f"✅ Datasets verified. Tracking {len(ALL_UNIQUE_SKILLS)} target skills across {len(SKILL_ROLE_MATRIX)} roles.")
except Exception as e:
    print(f"❌ Initialization Error: {e}")

# --- 3. DATA CONTRACT SCHEMAS ---
class ResumeRequest(BaseModel):
    raw_text: str

class ChatRequest(BaseModel):
    raw_text: str
    question: str

class GradeRequest(BaseModel):
    candidate_answer: str
    golden_answer: str

class LeaderboardEntry(BaseModel):
    candidate_name: str
    predicted_role: str
    resume_score: float
    interview_score: float

# --- 4. ENDPOINTS ---

@app.post("/screen-resume")
def screen_resume(req: ResumeRequest):
    """
    Parses skills and total timeline indicators entirely locally via target regex profiles.
    """
    if not req.raw_text:
        return {"extracted_skills": [], "predicted_role": "General Technical", "match_percentage": 0.0, "missing_skills": [], "years_experience": 0.0}

    text_lower = req.raw_text.lower()
    candidate_skills = set()

    # 1. Regex Skill Mapping Loop
    for skill in ALL_UNIQUE_SKILLS:
        escaped_skill = re.escape(skill)
        if skill.isalnum():
            pattern = rf"\b{escaped_skill}\b"
        else:
            pattern = rf"(?:^|\s|[^a-zA-Z0-9]){escaped_skill}(?:$|\s|[^a-zA-Z0-9])"
            
        if re.search(pattern, text_lower):
            candidate_skills.add(skill)

    # 2. Regex Experience Timeline Grabber
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

    # 3. Best Matching Role Calculation Matrix
    best_role = "General Technical"
    highest_match = 0.0
    missing = []
    
    for role, required in SKILL_ROLE_MATRIX.items():
        if not required: continue
        match_pct = (len(candidate_skills.intersection(required)) / len(required)) * 100
        if match_pct > highest_match:
            highest_match = match_pct
            best_role = role
            missing = list(required - candidate_skills)
            
    return {
        "extracted_skills": list(candidate_skills),
        "predicted_role": best_role,
        "match_percentage": round(highest_match, 2),
        "missing_skills": missing,
        "years_experience": years_exp
    }

@app.post("/chat-resume")
def chat_resume(req: ChatRequest):
    """
    Executes deep semantic text chunking with a 1500-character window and 300-character 
    overlap. Instructs Gemini to provide smart, articulated syntheses instead of raw copy-pasting.
    """
    # 1. Sliding window chunking configuration
    chunk_size = 1500
    step = 1200  # chunk_size - overlap (300)
    chunks = []
    text_len = len(req.raw_text)
    
    if text_len <= chunk_size:
        chunks = [req.raw_text]
    else:
        for i in range(0, text_len, step):
            chunk = req.raw_text[i:i+chunk_size]
            if chunk.strip():
                chunks.append(chunk)

    if not chunks: 
        return {"answer": "No resume text available to search."}

    # 2. Vector embedding matching
    chunk_embeddings = embedding_model.encode(chunks, convert_to_tensor=True)
    query_embedding = embedding_model.encode(req.question, convert_to_tensor=True)
    
    hits = util.semantic_search(query_embedding, chunk_embeddings, top_k=3)[0]
    top_chunks = [chunks[hit['corpus_id']] for hit in hits]
    context = "\n... \n".join(top_chunks)
    
    # 3. Refined prompt for true natural language synthesis
    prompt = f"""
    You are an intelligent HR assistant analyzing a candidate's resume context.
    Review the Context elements below and answer the User Question articulately.
    
    CRITICAL INSTRUCTIONS:
    - If the user asks for a summary, project breakdown, or overview, do NOT just copy-paste the raw bullet points or text exactly as they are. Instead, read the details and rewrite them into a clean, professional narrative summary using paragraphs and your own bullet points.
    - Stay 100% truthful to the context. Do not invent skills, numbers, or technologies that are not mentioned.
    - If the question cannot be answered using the provided context, reply exactly: "I could not locate specific verified validations for this prompt within the candidate file."

    Context:
    {context}

    Question: {req.question}
    """
    try:
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        return {"answer": response.text}
    except Exception as e:
        return {"answer": f"Chat processing failed due to API status connection issues: {e}"}


@app.get("/get-questions")
def get_questions(role: str = Query(...)):
    """
    Gathers all questions across required core skills and pools them together 
    to deliver an assessment containing exactly 10 custom questions.
    """
    required_skills = list(SKILL_ROLE_MATRIX.get(role, {"python", "sql", "git"}))
    pool = []
    
    # Pool all valid matching questions from your JSON bank
    for skill in required_skills:
        if skill in QUESTION_BANK:
            for q_data in QUESTION_BANK[skill]:
                pool.append({"topic": skill.upper(), "q": q_data["q"], "a": q_data["a"]})
                
    # Fallback safety net: if the role has no questions, populate with standard core concepts
    if not pool:
        for skill in ["python", "sql", "git"]:
            if skill in QUESTION_BANK:
                for q_data in QUESTION_BANK[skill]:
                    pool.append({"topic": skill.upper(), "q": q_data["q"], "a": q_data["a"]})

    # Ensure the examination array contains exactly 10 questions
    if len(pool) >= 10:
        custom_exam = random.sample(pool, 10)
    else:
        # If your JSON question pool has less than 10 items total, fill the remainder safely
        custom_exam = list(pool)
        while len(custom_exam) < 10 and pool:
            custom_exam.append(random.choice(pool))
            
    return custom_exam

@app.post("/grade-answer")
def grade_answer(req: GradeRequest):
    if len(req.candidate_answer.split()) < 3: return {"score": 0.0, "feedback": "Answer too short."}
    cand_vec = embedding_model.encode(req.candidate_answer, convert_to_tensor=True)
    gold_vec = embedding_model.encode(req.golden_answer, convert_to_tensor=True)
    similarity = util.cos_sim(cand_vec, gold_vec).item()
    return {"score": max(0, min(100, round(similarity * 100)))}

@app.post("/submit-leaderboard")
def submit_leaderboard(entry: LeaderboardEntry):
    data = {"Candidate Name": [entry.candidate_name], "Predicted Role": [entry.predicted_role], "Resume Match %": [round(entry.resume_score, 1)], "Interview Score %": [round(entry.interview_score, 1)]}
    df_new = pd.DataFrame(data)
    if os.path.exists(LEADERBOARD_FILE):
        df_existing = pd.read_csv(LEADERBOARD_FILE)
        pd.concat([df_existing, df_new], ignore_index=True).to_csv(LEADERBOARD_FILE, index=False)
    else:
        df_new.to_csv(LEADERBOARD_FILE, index=False)
    return {"status": "success"}

@app.get("/get-leaderboard")
def get_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        return pd.read_csv(LEADERBOARD_FILE).to_dict(orient="records")
    return []