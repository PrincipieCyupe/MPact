"""Seed the database with demo jobs and sample applicants from CSV."""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from extensions import db
from models import Job, Applicant

DEMO_JOBS = [
    {
        "title": "Senior Backend Engineer",
        "department": "Engineering",
        "location": "Kigali",
        "employment_type": "Full-time",
        "seniority": "Senior",
        "description": (
            "We're looking for a Senior Backend Engineer to design and ship "
            "scalable APIs that power our core platform. You'll work with "
            "Python / Flask, PostgreSQL, and Docker in a CI/CD-driven "
            "workflow. Ideal candidates thrive in cross-functional squads "
            "and care deeply about clean architecture, testing, and "
            "operational excellence. Experience with fintech or "
            "high-throughput systems is a strong plus."
        ),
        "required_skills": "Python, Flask, PostgreSQL, Docker, REST APIs",
        "min_years_experience": 4,
        "required_education": "bachelors",
        "weight_skills": 40,
        "weight_experience": 30,
        "weight_education": 15,
        "weight_projects": 15,
    },
    {
        "title": "Data Scientist — Risk & Fraud",
        "department": "Data",
        "location": "Kigali",
        "employment_type": "Full-time",
        "seniority": "Mid-level",
        "description": (
            "Join our Data team to build ML models that detect fraud and "
            "assess credit risk across mobile-money channels. You'll own "
            "the full modelling lifecycle — data cleaning, feature "
            "engineering, training, evaluation, and production deployment. "
            "We value pragmatism: Pandas + scikit-learn shipped fast beats "
            "a perfect model shipped never."
        ),
        "required_skills": "Python, Pandas, Machine Learning, SQL, Flask",
        "min_years_experience": 3,
        "required_education": "bachelors",
        "weight_skills": 35,
        "weight_experience": 25,
        "weight_education": 20,
        "weight_projects": 20,
    },
    {
        "title": "Frontend Developer (React)",
        "department": "Engineering",
        "location": "Remote",
        "employment_type": "Full-time",
        "seniority": "Mid-level",
        "description": (
            "We need a product-minded Frontend Developer to craft "
            "delightful interfaces with React, TypeScript, and modern CSS. "
            "You'll collaborate closely with designers and backend engineers "
            "to ship pixel-perfect, accessible UIs. Bonus if you have "
            "experience with Next.js or mobile-responsive dashboards."
        ),
        "required_skills": "JavaScript, React, Node.js, CSS, HTML",
        "min_years_experience": 3,
        "required_education": "bachelors",
        "weight_skills": 45,
        "weight_experience": 25,
        "weight_education": 10,
        "weight_projects": 20,
    },
    {
        "title": "DevOps / Platform Engineer",
        "department": "Infrastructure",
        "location": "Remote",
        "employment_type": "Contract",
        "seniority": "Senior",
        "description": (
            "Own and evolve our cloud infrastructure on GCP. You'll build "
            "CI/CD pipelines, manage Kubernetes clusters, implement IaC "
            "with Terraform, and ensure 99.9% uptime. Deep Linux, Docker, "
            "and networking knowledge required. Experience with fintech "
            "compliance (PCI-DSS, SOC 2) is a bonus."
        ),
        "required_skills": "Docker, Kubernetes, GCP, Linux, Python",
        "min_years_experience": 5,
        "required_education": "bachelors",
        "weight_skills": 45,
        "weight_experience": 35,
        "weight_education": 5,
        "weight_projects": 15,
    },
]

# Mapping: applicant name -> which job indices they apply to (0-based)
APPLICANT_JOB_MAP = {
    "Aline Uwase":       [0],
    "Eric Mugisha":      [0],
    "Patrick Niyonsaba":  [2],
    "Diane Mukamana":    [1],
    "Jean Bosco Habimana": [0],
    "Sarah Ingabire":    [0, 3],
    "Kevin Ndayisaba":   [2],
    "Grace Umutoni":     [0],
    "Eric Tuyishime":    [3],
    "Linda Iradukunda":  [2],
    "Olivier Bizimana":  [0, 1],
    "Christine Mutesi":  [2],
}

EDU_LEVEL_MAP = {
    "bsc": "bachelors",
    "msc": "masters",
    "phd": "phd",
    "diploma": "diploma",
}


def _guess_edu_level(edu_str):
    edu_lower = (edu_str or "").lower()
    for key, val in EDU_LEVEL_MAP.items():
        if key in edu_lower:
            return val
    if "progress" in edu_lower:
        return "none"
    return "bachelors"


def seed():
    app = create_app()
    with app.app_context():
        if Job.query.count() > 0:
            print("[seed] Database already has data — skipping. Delete instance/mpact.db to re-seed.")
            return

        # Create jobs
        jobs = []
        for jd in DEMO_JOBS:
            j = Job(**jd, is_published=True)
            db.session.add(j)
            jobs.append(j)
        db.session.flush()  # get IDs

        # Load CSV applicants
        csv_path = os.path.join(os.path.dirname(__file__), "sample_data", "applicants_sample.csv")
        if not os.path.exists(csv_path):
            print(f"[seed] CSV not found at {csv_path}")
            db.session.commit()
            return

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row["full_name"].strip()
                target_indices = APPLICANT_JOB_MAP.get(name, [0])
                for idx in target_indices:
                    if idx >= len(jobs):
                        continue
                    a = Applicant(
                        job_id=jobs[idx].id,
                        full_name=name,
                        email=row.get("email", "").strip(),
                        phone=row.get("phone", "").strip(),
                        location=row.get("location", "").strip(),
                        skills=row.get("skills", "").strip(),
                        years_experience=float(row.get("years_experience") or 0),
                        education=row.get("education", "").strip(),
                        education_level=_guess_edu_level(row.get("education", "")),
                        projects=row.get("projects", "").strip(),
                        project_count=int(row.get("project_count") or 0),
                        source="seed",
                        status="new",
                    )
                    db.session.add(a)

        db.session.commit()
        total_applicants = Applicant.query.count()
        print(f"[seed] Created {len(jobs)} jobs and {total_applicants} applicant records.")


if __name__ == "__main__":
    seed()
