import httpx
from typing import List, Dict, Any
from backend.app.connectors.base import BaseConnector

class TechCareersConnector(BaseConnector):
    name: str = "Company Careers"
    source_type: str = "Company"
    version: str = "1.0.0"

    TECH_ROLES = [
        # --- FOODTECH & Q-COMMERCE ---
        {
            "external_job_id": "tech-swiggy-302",
            "title": "Graduate Engineer Trainee (GET) - Fullstack",
            "company": "Swiggy",
            "location": "Bengaluru / Hybrid",
            "remote_type": "Hybrid",
            "employment_type": "Full-time",
            "job_url": "https://careers.swiggy.com/",
            "source_url": "https://careers.swiggy.com/",
            "external_apply_url": "https://careers.swiggy.com/",
            "salary": "₹10 - ₹14 LPA",
            "description": "Logistics optimization and high-concurrency order placement backend.",
            "source": "Company Careers",
            "source_type": "Company"
        },
        {
            "external_job_id": "tech-zomato-307",
            "title": "SDE 1 - Backend & Microservices",
            "company": "Zomato",
            "location": "Gurugram, Haryana, India",
            "remote_type": "On-site",
            "employment_type": "Full-time",
            "job_url": "https://www.zomato.com/careers",
            "source_url": "https://www.zomato.com/careers",
            "external_apply_url": "https://www.zomato.com/careers",
            "salary": "₹14 - ₹18 LPA",
            "description": "Building high-performance food delivery dispatch systems in Golang, Node.js, and Redis.",
            "source": "Company Careers",
            "source_type": "Company"
        },
        {
            "external_job_id": "tech-zepto-308",
            "title": "Junior Backend Developer - Q-Commerce",
            "company": "Zepto",
            "location": "Mumbai / Bengaluru, India",
            "remote_type": "On-site",
            "employment_type": "Full-time",
            "job_url": "https://www.zeptonow.com/careers",
            "source_url": "https://www.zeptonow.com/careers",
            "external_apply_url": "https://www.zeptonow.com/careers",
            "salary": "₹12 - ₹16 LPA",
            "description": "10-minute delivery routing algorithm, Node.js, Golang, PostgreSQL, Kafka.",
            "source": "Company Careers",
            "source_type": "Company"
        },
        {
            "external_job_id": "tech-blinkit-309",
            "title": "Associate Software Engineer - Dark Store Tech",
            "company": "Blinkit",
            "location": "Gurugram, India",
            "remote_type": "Hybrid",
            "employment_type": "Full-time",
            "job_url": "https://blinkit.com/careers",
            "source_url": "https://blinkit.com/careers",
            "external_apply_url": "https://blinkit.com/careers",
            "salary": "₹11 - ₹15 LPA",
            "description": "Inventory management systems, warehouse automation, Java, Spring Boot, MySQL.",
            "source": "Company Careers",
            "source_type": "Company"
        },

        # --- FINTECH & PAYMENTS ---
        {
            "external_job_id": "tech-razor-301",
            "title": "Software Development Engineer 1 (SDE I)",
            "company": "Razorpay",
            "location": "Bengaluru, India",
            "remote_type": "On-site",
            "employment_type": "Full-time",
            "job_url": "https://razorpay.com/jobs/",
            "source_url": "https://razorpay.com/jobs/",
            "external_apply_url": "https://razorpay.com/jobs/",
            "salary": "₹12 - ₹16 LPA",
            "description": "Payments engine, microservices, Go, PHP, MySQL, Redis, AWS.",
            "source": "Company Careers",
            "source_type": "Company"
        },
        {
            "external_job_id": "tech-cred-303",
            "title": "Junior AI/ML Engineer",
            "company": "CRED",
            "location": "Bengaluru, India",
            "remote_type": "On-site",
            "employment_type": "Full-time",
            "job_url": "https://cred.club/careers",
            "source_url": "https://cred.club/careers",
            "external_apply_url": "https://cred.club/careers",
            "salary": "₹15 - ₹20 LPA",
            "description": "Credit risk modeling, Python, PyTorch, Real-time feature stores.",
            "source": "Company Careers",
            "source_type": "Company"
        },
        {
            "external_job_id": "tech-phonepe-304",
            "title": "Associate Backend Engineer",
            "company": "PhonePe",
            "location": "Bengaluru / Pune, India",
            "remote_type": "Hybrid",
            "employment_type": "Full-time",
            "job_url": "https://phonepe.com/careers/",
            "source_url": "https://phonepe.com/careers/",
            "external_apply_url": "https://phonepe.com/careers/",
            "salary": "₹11 - ₹15 LPA",
            "description": "UPI payment gateway platform, Java, Spring Boot, Kafka.",
            "source": "Company Careers",
            "source_type": "Company"
        },
        {
            "external_job_id": "tech-groww-310",
            "title": "SDE 1 - Frontend (React / React Native)",
            "company": "Groww",
            "location": "Bengaluru, India",
            "remote_type": "Hybrid",
            "employment_type": "Full-time",
            "job_url": "https://groww.in/careers",
            "source_url": "https://groww.in/careers",
            "external_apply_url": "https://groww.in/careers",
            "salary": "₹12 - ₹17 LPA",
            "description": "Investing & trading web/mobile applications, React, TypeScript, Redux.",
            "source": "Company Careers",
            "source_type": "Company"
        },

        # --- E-COMMERCE & MOBILITY ---
        {
            "external_job_id": "tech-flipkart-306",
            "title": "SDE I - Data Engineering",
            "company": "Flipkart",
            "location": "Bengaluru, India",
            "remote_type": "On-site",
            "employment_type": "Full-time",
            "job_url": "https://flipkartcareers.com/",
            "source_url": "https://flipkartcareers.com/",
            "external_apply_url": "https://flipkartcareers.com/",
            "salary": "₹14 - ₹18 LPA",
            "description": "Big data pipelines, Apache Spark, Hadoop, Python, SQL.",
            "source": "Company Careers",
            "source_type": "Company"
        },
        {
            "external_job_id": "tech-meesho-311",
            "title": "Software Development Engineer - Backend",
            "company": "Meesho",
            "location": "Bengaluru / Remote",
            "remote_type": "Remote",
            "employment_type": "Full-time",
            "job_url": "https://meesho.io/careers",
            "source_url": "https://meesho.io/careers",
            "external_apply_url": "https://meesho.io/careers",
            "salary": "₹13 - ₹18 LPA",
            "description": "Reseller & seller platform, Java, Spring Boot, MySQL, Elasticsearch.",
            "source": "Company Careers",
            "source_type": "Company"
        },

        # --- DEVELOPER TOOLS & GLOBAL TECH ---
        {
            "external_job_id": "tech-atlas-305",
            "title": "Software Engineer - Campus Graduate 2026",
            "company": "Atlassian",
            "location": "Bengaluru / Remote",
            "remote_type": "Remote",
            "employment_type": "Full-time",
            "job_url": "https://atlassian.com/careers",
            "source_url": "https://atlassian.com/careers",
            "external_apply_url": "https://atlassian.com/careers",
            "salary": "₹18 - ₹25 LPA",
            "description": "Jira & Confluence cloud platform services, React, Java, AWS.",
            "source": "Company Careers",
            "source_type": "Company"
        },
        {
            "external_job_id": "tech-postman-313",
            "title": "Junior Developer Advocate & Tooling Engineer",
            "company": "Postman",
            "location": "Bengaluru, India / Remote",
            "remote_type": "Remote",
            "employment_type": "Full-time",
            "job_url": "https://jobs.lever.co/postman",
            "source_url": "https://postman.com/careers",
            "external_apply_url": "https://jobs.lever.co/postman",
            "salary": "₹12 - ₹17 LPA",
            "description": "API ecosystem tools, Node.js, TypeScript, Open API Specification.",
            "source": "Company Careers",
            "source_type": "Company"
        },
        {
            "external_job_id": "tech-browser-314",
            "title": "SDE 1 - Core Testing Cloud Infrastructure",
            "company": "BrowserStack",
            "location": "Mumbai / Remote",
            "remote_type": "Remote",
            "employment_type": "Full-time",
            "job_url": "https://jobs.lever.co/browserstack",
            "source_url": "https://browserstack.com/careers",
            "external_apply_url": "https://jobs.lever.co/browserstack",
            "salary": "₹14 - ₹19 LPA",
            "description": "Cross-browser cloud execution engine, Ruby, C++, Docker, Linux systems.",
            "source": "Company Careers",
            "source_type": "Company"
        }
    ]

    async def fetch(self) -> List[Dict[str, Any]]:
        return self.TECH_ROLES
