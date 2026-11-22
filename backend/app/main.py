
import os
import re
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

# =====================================
# ENVIRONMENT
# =====================================

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

app = FastAPI(title="AI Job Recommender")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================
# DATABASE CONNECTION
# =====================================

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "ai_job_recommender"),
    )


# =====================================
# SKILLS DATABASE
# =====================================

SKILLS = [
    "python", "java", "c++", "javascript",
    "html", "css", "react", "sql", "mysql",
    "git", "github", "dsa", "algorithms",
    "data structures", "oops", "oop", "dbms",
    "operating systems", "computer networks",
    "pandas", "numpy", "matplotlib",
    "machine learning", "scikit-learn",
    "deep learning", "artificial intelligence",
    "data science", "excel", "power bi",
    "tableau", "fastapi", "flask",
    "aws", "azure", "docker"
]


LEARNING_SUGGESTIONS = {
    "python": "Practice Python basics, functions, OOP and problem solving.",
    "sql": "Practice SELECT, JOIN, GROUP BY and subqueries.",
    "mysql": "Learn database design, queries and joins.",
    "dsa": "Practice arrays, strings, searching and sorting.",
    "machine learning": "Learn supervised and unsupervised learning.",
    "pandas": "Practice data cleaning and data analysis.",
    "numpy": "Learn arrays, indexing and numerical operations.",
    "excel": "Learn formulas, pivot tables and data analysis.",
    "git": "Practice Git commands and version control.",
    "fastapi": "Build REST APIs using FastAPI.",
    "html": "Learn semantic HTML and page structure.",
    "css": "Practice layouts, flexbox and responsive design.",
    "javascript": "Learn DOM, functions and asynchronous JavaScript.",
    "react": "Learn components, props and state.",
    "java": "Practice OOP and Java programming.",
    "oop": "Learn classes, objects, inheritance and polymorphism.",
    "oops": "Learn classes, objects, inheritance and polymorphism.",
    "data science": "Practice data analysis and machine learning projects.",
    "artificial intelligence": "Study AI concepts and practical projects.",
    "scikit-learn": "Build ML models using Scikit-Learn.",
    "deep learning": "Learn neural networks and deep learning basics.",
    "power bi": "Practice dashboards and data visualization.",
    "docker": "Learn containers and basic Docker commands.",
    "aws": "Learn cloud fundamentals and AWS services.",
    "azure": "Learn cloud computing using Azure.",
    "flask": "Build web applications using Flask.",
    "dbms": "Learn SQL, normalization and DBMS concepts.",
    "algorithms": "Practice searching, sorting and algorithm analysis.",
    "data structures": "Learn arrays, stacks, queues, trees and graphs.",
    "computer networks": "Study TCP/IP, HTTP, DNS and networking basics.",
    "operating systems": "Study processes, threads, memory and scheduling.",
    "c++": "Practice C++ programming and STL.",
    "matplotlib": "Create charts and data visualizations.",
    "tableau": "Practice interactive dashboards in Tableau.",
    "github": "Practice repositories, commits and collaboration."
}


# =====================================
# RESUME TEXT EXTRACTION
# =====================================

def extract_resume_text(filename, content):

    extension = Path(filename or "").suffix.lower()

    # TXT
    if extension == ".txt":
        return content.decode("utf-8", errors="ignore")

    # PDF
    if extension == ".pdf":
        try:
            from pypdf import PdfReader
            import io

            reader = PdfReader(io.BytesIO(content))

            return " ".join(
                page.extract_text() or ""
                for page in reader.pages
            )

        except Exception as e:
            raise ValueError(
                "PDF reading failed. Check pypdf installation."
            ) from e

    # DOCX
    if extension == ".docx":
        try:
            from docx import Document
            import io

            document = Document(io.BytesIO(content))

            return " ".join(
                paragraph.text
                for paragraph in document.paragraphs
            )

        except Exception as e:
            raise ValueError(
                "DOCX reading failed. Check python-docx installation."
            ) from e

    raise ValueError(
        "Unsupported file. Upload PDF, DOCX or TXT."
    )


# =====================================
# SKILLS DETECTION
# =====================================

def detect_skills(resume_text):

    text = resume_text.lower()
    detected = []

    for skill in SKILLS:

        pattern = (
            r"(?<![a-z0-9+#])"
            + re.escape(skill.lower())
            + r"(?![a-z0-9+#])"
        )

        if re.search(pattern, text):
            detected.append(skill)

    return detected


# =====================================
# RESUME SCORE
# =====================================

def calculate_resume_score(skills):

    total_skills = len(SKILLS)

    if total_skills == 0:
        return 0

    score = round(
        (len(skills) / total_skills) * 100
    )

    return min(score, 100)


# =====================================
# DATABASE TEST
# =====================================

@app.get("/db-test")
def db_test():

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT DATABASE()")
        db_name = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return {
            "success": True,
            "message": "Database connected successfully",
            "database": db_name
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


# =====================================
# GET JOBS
# =====================================

@app.get("/jobs")
def get_jobs():

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM jobs")
        jobs = cursor.fetchall()

        cursor.close()
        conn.close()

        return {
            "success": True,
            "count": len(jobs),
            "jobs": jobs
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


# =====================================
# UPLOAD RESUME
# =====================================

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):

    try:
        content = await file.read()

        return {
            "success": True,
            "filename": file.filename,
            "message": "Resume uploaded successfully",
            "size": len(content)
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


# =====================================
# MATCH JOBS
# =====================================

@app.post("/match-jobs")
async def match_jobs(file: UploadFile = File(...)):

    conn = None
    cursor = None

    try:

        content = await file.read()

        resume_text = extract_resume_text(
            file.filename,
            content
        ).lower()

        detected_skills = detect_skills(resume_text)

        resume_score = calculate_resume_score(
            detected_skills
        )

        # Connect database
        conn = get_db_connection()

        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM jobs")

        jobs = cursor.fetchall()

        recommendations = []

        # Match each job
        for job in jobs:

            job_title = str(
                job.get("job_title", "")
            )

            company = str(
                job.get("company", "")
            )

            required_skills_text = str(
                job.get("required_skills", "")
            ).lower()

            required_skills = [
                skill.strip()
                for skill in required_skills_text.split(",")
                if skill.strip()
            ]

            matched_skills = [
                skill
                for skill in required_skills
                if skill.lower() in detected_skills
            ]

            missing_skills = [
                skill
                for skill in required_skills
                if skill.lower() not in detected_skills
            ]

            total_required = len(required_skills)

            if total_required > 0:

                match_percentage = round(
                    (len(matched_skills) / total_required) * 100
                )

            else:

                match_percentage = 0

            what_to_learn = []

            for skill in missing_skills:

                suggestion = LEARNING_SUGGESTIONS.get(
                    skill.lower(),
                    f"Practice {skill} and build a small project."
                )

                what_to_learn.append({
                    "skill": skill,
                    "suggestion": suggestion
                })

            job["matched_skills"] = matched_skills
            job["missing_skills"] = missing_skills
            job["match_percentage"] = match_percentage
            job["what_to_learn"] = what_to_learn

            recommendations.append(job)

        # Sort by match percentage
        recommendations.sort(
            key=lambda job: job["match_percentage"],
            reverse=True
        )

        return {
            "success": True,
            "resume_score": resume_score,
            "detected_skills": detected_skills,
            "total_jobs_checked": len(jobs),
            "recommendations": recommendations
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }

    finally:

        if cursor is not None:
            cursor.close()

        if conn is not None:
            conn.close()
