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
