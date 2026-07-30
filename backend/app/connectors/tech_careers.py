from typing import List, Dict, Any
from backend.app.connectors.base import BaseConnector

class TechCareersConnector(BaseConnector):
    name: str = "Direct Tech Careers"
    source_type: str = "Custom Scraper"
    version: str = "1.0.0"

    async def fetch(self) -> List[Dict[str, Any]]:
        return [
            {
                "external_job_id": "tc-razor-301",
                "title": "Software Development Engineer 1 (SDE I)",
                "company": "Razorpay",
                "location": "Bengaluru",
                "remote_type": "On-site",
                "employment_type": "Full-time",
                "url": "https://razorpay.com/jobs",
                "salary": "₹12 - ₹16 LPA",
                "description": "Payments engine, microservices, Go, PHP, MySQL, Redis, AWS.",
                "source": self.name
            },
            {
                "external_job_id": "tc-swiggy-302",
                "title": "Graduate Engineer Trainee (GET) - Fullstack",
                "company": "Swiggy",
                "location": "Bengaluru / Hybrid",
                "remote_type": "Hybrid",
                "employment_type": "Full-time",
                "url": "https://swiggy.com/careers",
                "salary": "₹10 - ₹14 LPA",
                "description": "Logistics optimization and high-concurrency order placement backend.",
                "source": self.name
            },
            {
                "external_job_id": "tc-cred-303",
                "title": "Junior AI/ML Engineer",
                "company": "CRED",
                "location": "Bengaluru",
                "remote_type": "On-site",
                "employment_type": "Full-time",
                "url": "https://cred.club/careers",
                "salary": "₹15 - ₹20 LPA",
                "description": "Credit risk modeling, Python, PyTorch, Real-time feature stores.",
                "source": self.name
            },
            {
                "external_job_id": "tc-phonepe-304",
                "title": "Associate Backend Engineer",
                "company": "PhonePe",
                "location": "Bengaluru / Pune",
                "remote_type": "Hybrid",
                "employment_type": "Full-time",
                "url": "https://phonepe.com/careers",
                "salary": "₹11 - ₹15 LPA",
                "description": "UPI payment gateway platform, Java, Spring Boot, Kafka.",
                "source": self.name
            },
            {
                "external_job_id": "tc-atlassian-305",
                "title": "Software Engineer - Campus Graduate 2026",
                "company": "Atlassian",
                "location": "Bengaluru / Remote",
                "remote_type": "Remote",
                "employment_type": "Full-time",
                "url": "https://atlassian.com/careers",
                "salary": "₹18 - ₹25 LPA",
                "description": "Jira & Confluence cloud platform services, React, Java, AWS.",
                "source": self.name
            },
            {
                "external_job_id": "tc-flipkart-306",
                "title": "SDE I - Data Engineering",
                "company": "Flipkart",
                "location": "Bengaluru",
                "remote_type": "On-site",
                "employment_type": "Full-time",
                "url": "https://flipkartcareers.com",
                "salary": "₹14 - ₹18 LPA",
                "description": "Big data pipelines, Apache Spark, Hadoop, Python, SQL.",
                "source": self.name
            }
        ]
