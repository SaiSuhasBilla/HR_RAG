# AI HR Platform: Retrieval-Augmented Generation (RAG)

An intelligent, end-to-end recruitment assistant engineered to streamline candidate evaluation. By utilizing **Retrieval-Augmented Generation (RAG)**, this platform bridges the gap between static job descriptions and dynamic candidate insights, ensuring highly accurate and context-aware interview simulations.


Key Capabilities
🔍 Intelligent RAG Pipeline
Contextual Retrieval: Dynamically fetches relevant hiring criteria and candidate qualifications from your local datasets.

Semantic Analysis: Processes complex HR queries to provide nuanced feedback rather than keyword-based matching.

📊 Automated Assessment Logic
Skill Alignment: Compares candidate input against standardized job requirements found in your it_jobs_required_skills.csv and leaderboard.csv files.

Objective Scoring: Provides consistent, data-driven evaluations of interview performance.

💻 System Architecture
Modular Design: A robust separation of concerns with a dedicated backend for RAG orchestration and a frontend for interactive user sessions.

Data-Driven Core: Leverages integrated JSON and CSV data stores to drive the logic for candidate character guessing and interview questioning.

Technical Highlights
Backend Engineering: Developed using a custom Python pipeline to handle data retrieval and chatbot logic.

Interactive UI: Built with Streamlit to provide a seamless, responsive experience for both HR professionals and candidates.

Scalability: Structured to support future growth, with clean separation between frontend services and backend API endpoints.


## Project Directory Structure
```text
ragg/
├── backend/          # FastAPI/Python logic and RAG implementation
│   ├── it_jobs_required_skills.csv
│   ├── leaderboard.csv
│   ├── questions.json
│   └── main.py
├── frontend/         # Streamlit-based UI for candidates and HR
│   ├── utils/
│   ├── views/
│   └── main.py
├── .gitignore        
└── README.md

## Project Interface

**1. Login Portal**
<img width="600" alt="AI_HR_LOGIN" src="https://github.com/user-attachments/assets/46a8cbbb-099f-4849-8cdc-ed7237c10f89" />

**2. Recruiter Dashboard**
<img width="600" alt="HR_RECRUITER_DASHBOARD" src="https://github.com/user-attachments/assets/8034feb4-f74c-4333-ae0d-4e7eadeceddd" />

**3. Recruiter RAG Chatbot**
<img width="600" alt="HR_RAG_QUERY" src="https://github.com/user-attachments/assets/56ef6b10-a3df-41ab-94bf-2aa6504b0a08" />

**4. Candidate View**
<img width="600" alt="Screenshot_8-7-2026_173124_localhost" src="https://github.com/user-attachments/assets/af8ac79a-de91-42a0-8e19-6dbdb268ac50" />

**5. Candidate Exam Portal**
<img width="600" alt="Screenshot_8-7-2026_173723_localhost" src="https://github.com/user-attachments/assets/c8d886a4-dc5d-4437-82f5-638cc0058e57" />

**6. Leaderboard**
<img width="600" alt="HR_LEADERBOARD" src="https://github.com/user-attachments/assets/802e548b-d941-4c60-8488-66236b2f4476" />

