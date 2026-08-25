import io
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
import PyPDF2

class ResumeParserEngine:
    """
    Structured Resume Parsing Engine for PDF, DOCX, and text resumes.
    Extracts candidate profile, skills, experience level, degree, preferred roles, and projects.
    """

    TECH_KEYWORDS = {
        "programming_languages": [
            "Python", "Java", "C++", "C#", "C", "Go", "Golang", "Rust", "TypeScript", "JavaScript",
            "SQL", "R", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "Dart", "HTML", "CSS"
        ],
        "frameworks": [
            "React", "React.js", "Next.js", "Angular", "Vue", "Vue.js", "FastAPI", "Django", "Flask",
            "Express", "Express.js", "Node.js", "Spring Boot", "Spring", "Redux", "Tailwind",
            "TailwindCSS", "Bootstrap", "GraphQL", "REST API", "RESTful APIs", "Microservices"
        ],
        "databases": [
            "PostgreSQL", "Postgres", "MySQL", "MongoDB", "Redis", "SQLite", "DynamoDB",
            "Cassandra", "Elasticsearch", "Neo4j", "Firebase"
        ],
        "cloud_technologies": [
            "AWS", "Amazon Web Services", "GCP", "Google Cloud", "Azure", "Docker", "Kubernetes",
            "K8s", "Terraform", "Serverless", "Lambda", "EC2", "S3", "Cloudflare", "CI/CD", "Git", "GitHub"
        ],
        "ml_ai_technologies": [
            "Machine Learning", "Deep Learning", "PyTorch", "TensorFlow", "Scikit-learn", "Keras",
            "NLP", "Natural Language Processing", "Computer Vision", "OpenCV", "LLM", "LangChain",
            "Transformers", "HuggingFace", "RAG", "Pandas", "NumPy", "Data Science", "AI"
        ],
        "core_cs": [
            "Data Structures", "Algorithms", "System Design", "Object Oriented Programming", "OOP",
            "Operating Systems", "Computer Networks", "DBMS", "Linux", "Agile", "Scrum"
        ]
    }

    @classmethod
    def extract_text_from_pdf(cls, file_bytes: bytes) -> str:
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            extracted = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted.append(text)
            return "\n".join(extracted)
        except Exception as e:
            print(f"[ResumeParser] PDF extraction error: {e}")
            return ""

    @classmethod
    def extract_text_from_docx(cls, file_bytes: bytes) -> str:
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                xml_content = z.read("word/document.xml")
                tree = ET.fromstring(xml_content)
                texts = [node.text for node in tree.iter() if node.text]
                return " ".join(texts)
        except Exception as e:
            print(f"[ResumeParser] DOCX extraction error: {e}")
            return ""

    @classmethod
    def extract_text(cls, file_bytes: bytes, filename: str) -> str:
        ext = filename.lower().split(".")[-1] if "." in filename else ""
        if ext == "pdf":
            text = cls.extract_text_from_pdf(file_bytes)
        elif ext in ["docx", "doc"]:
            text = cls.extract_text_from_docx(file_bytes)
        else:
            try:
                text = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text = file_bytes.decode("latin-1", errors="ignore")

        return text.strip()

    @classmethod
    def parse_profile(cls, resume_text: str, filename: Optional[str] = None) -> Dict[str, Any]:
        text_lower = resume_text.lower()
        lines = [line.strip() for line in resume_text.split("\n") if line.strip()]

        # 1. Name & Contact
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', resume_text)
        email = email_match.group(0) if email_match else None

        phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', resume_text)
        phone = phone_match.group(0) if phone_match else None

        # Estimate name from first non-empty line
        name = "Candidate"
        if lines:
            first_line = lines[0]
            if len(first_line) < 40 and not any(kw in first_line.lower() for kw in ["resume", "curriculum", "email", "phone"]):
                name = first_line

        # 2. Extract Skills Across Categorized Dictionaries
        found_skills_categorized = {}
        all_skills_set = set()

        for category, kw_list in cls.TECH_KEYWORDS.items():
            found_in_cat = []
            for kw in kw_list:
                # Word boundary match
                pattern = r'\b' + re.escape(kw) + r'\b'
                if re.search(pattern, resume_text, re.IGNORECASE):
                    found_in_cat.append(kw)
                    all_skills_set.add(kw)
            found_skills_categorized[category] = found_in_cat

        # 3. Education & Degree
        degrees = []
        degree_patterns = [
            r'\b(b\.?tech|bachelor of technology)\b',
            r'\b(b\.?e|bachelor of engineering)\b',
            r'\b(m\.?tech|master of technology)\b',
            r'\b(m\.?s|master of science)\b',
            r'\b(b\.?s|bachelor of science)\b',
            r'\b(bca|mca|b\.?sc|m\.?sc)\b',
            r'\b(computer science|information technology|data science)\b'
        ]
        for dp in degree_patterns:
            m = re.search(dp, text_lower)
            if m:
                degrees.append(m.group(0).upper())

        degree = ", ".join(set(degrees)) if degrees else "B.Tech / Bachelor's in CS/Tech"

        # Graduation year extraction
        grad_year_match = re.search(r'\b(20[12][0-9])\b', resume_text)
        grad_year = grad_year_match.group(1) if grad_year_match else "2025/2026"

        # 4. Experience Level & YOE
        yoe = 0
        yoe_match = re.search(r'(\d+)\+?\s*(?:years?|yoe|yrs)', text_lower)
        if yoe_match:
            yoe = int(yoe_match.group(1))

        if "intern" in text_lower or "internship" in text_lower:
            exp_level = "Internship" if yoe == 0 else "Associate"
        elif yoe >= 4:
            exp_level = "Senior"
        elif yoe >= 2:
            exp_level = "Mid-Level"
        elif yoe >= 1:
            exp_level = "Associate"
        else:
            exp_level = "Fresher"

        # 5. Preferred Roles Inference
        preferred_roles = []
        if any(sk in all_skills_set for sk in ["Machine Learning", "PyTorch", "TensorFlow", "NLP", "Deep Learning", "AI"]):
            preferred_roles.append("Machine Learning Engineer / AI Engineer")
        if any(sk in all_skills_set for sk in ["FastAPI", "Django", "Node.js", "Spring Boot", "PostgreSQL", "SQL"]):
            preferred_roles.append("Backend Engineer (SDE 1 / SDE 2)")
        if any(sk in all_skills_set for sk in ["React", "Next.js", "TypeScript", "Tailwind", "Angular"]):
            preferred_roles.append("Frontend Developer")
        if any(sk in all_skills_set for sk in ["Docker", "Kubernetes", "AWS", "CI/CD", "DevOps"]):
            preferred_roles.append("DevOps / Cloud Engineer")

        if not preferred_roles:
            preferred_roles = ["Software Development Engineer (SDE 1)", "Full Stack Developer"]

        return {
            "name": name,
            "email": email,
            "phone": phone,
            "degree": degree,
            "graduation_year": grad_year,
            "experience_years": yoe,
            "experience_level": exp_level,
            "skills": sorted(list(all_skills_set)),
            "categorized_skills": found_skills_categorized,
            "preferred_roles": preferred_roles,
            "raw_text_length": len(resume_text),
            "filename": filename or "resume.pdf"
        }
