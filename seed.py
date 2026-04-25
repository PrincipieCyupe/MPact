"""Seed the database with Umurava-schema-compliant demo jobs and applicants."""
import json
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
            "engineering, training, evaluation, and production deployment."
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
            "to ship pixel-perfect, accessible UIs."
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
            "with Terraform, and ensure 99.9% uptime."
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

# Full Umurava-schema-compliant applicants
# All structured fields use schema-specified names:
#   skills[].name / skills[].level / skills[].yearsOfExperience
#   languages[].name / languages[].proficiency
#   experience[].company / experience[].role / experience[].startDate / experience[].endDate / experience[].isCurrent / experience[].description / experience[].technologies
#   education[].institution / education[].degree / education[].field / education[].startYear / education[].endYear
#   certifications[].name / certifications[].issuer / certifications[].date
#   projects[].name / projects[].description / projects[].technologies / projects[].role / projects[].link
#   availability.status / availability.type
#   socialLinks.linkedin / socialLinks.github / socialLinks.portfolio

DEMO_APPLICANTS = [
    # ── Job 0 applicants — Senior Backend Engineer ──────────────────────────
    {
        "job_index": 0,
        "full_name": "Aline Uwase",
        "email": "aline.uwase@example.rw",
        "phone": "+250 788 100 001",
        "location": "Kigali, Rwanda",
        "headline": "Senior Backend Engineer · Python & Cloud-Native Systems · 6 yrs",
        "bio": "Backend-focused engineer with six years building distributed APIs and data pipelines for fintech and e-commerce. I care about system reliability, clean interfaces, and teams that ship with intention.",
        "years_experience": 6.0,
        "education": "BSc Computer Science, University of Rwanda",
        "education_level": "bachelors",
        "structured_skills": [
            {"name": "Python",      "level": "Expert",        "yearsOfExperience": 6},
            {"name": "Flask",       "level": "Expert",        "yearsOfExperience": 5},
            {"name": "PostgreSQL",  "level": "Advanced",      "yearsOfExperience": 5},
            {"name": "Docker",      "level": "Advanced",      "yearsOfExperience": 4},
            {"name": "REST APIs",   "level": "Expert",        "yearsOfExperience": 6},
            {"name": "Redis",       "level": "Intermediate",  "yearsOfExperience": 3},
        ],
        "languages_data": [
            {"name": "Kinyarwanda", "proficiency": "native"},
            {"name": "English",     "proficiency": "fluent"},
            {"name": "French",      "proficiency": "professional"},
        ],
        "structured_experience": [
            {
                "company": "Equity Bank Rwanda",
                "role": "Senior Backend Engineer",
                "startDate": "2021-03",
                "endDate": None,
                "isCurrent": True,
                "description": "Designed core payment APIs handling 500K+ daily transactions. Reduced p99 latency by 40% through query optimization and Redis caching.",
                "technologies": ["Python", "Flask", "PostgreSQL", "Redis", "Docker"],
            },
            {
                "company": "Andela (Rwanda Hub)",
                "role": "Backend Engineer",
                "startDate": "2018-06",
                "endDate": "2021-02",
                "isCurrent": False,
                "description": "Built REST APIs and data ingestion pipelines for US-based SaaS clients. Mentored 3 junior engineers.",
                "technologies": ["Python", "Django", "PostgreSQL", "AWS"],
            },
        ],
        "structured_education": [
            {"institution": "University of Rwanda", "degree": "BSc", "field": "Computer Science", "startYear": 2014, "endYear": 2018},
        ],
        "certifications_data": [
            {"name": "AWS Certified Developer – Associate", "issuer": "Amazon Web Services", "date": "2022-05"},
            {"name": "Google Professional Cloud Developer",  "issuer": "Google Cloud",         "date": "2023-01"},
        ],
        "structured_projects": [
            {"name": "PayLink API Gateway", "description": "High-throughput payment routing service processing 500K+ daily transactions with <50ms latency.", "technologies": ["Python", "Flask", "PostgreSQL", "Redis"], "role": "Lead Backend Engineer", "link": "https://github.com/aline-uwase/paylink"},
            {"name": "Fraud Detection Pipeline", "description": "Real-time ML pipeline for mobile-money fraud detection, reducing false positives by 30%.", "technologies": ["Python", "Pandas", "scikit-learn", "Kafka"], "role": "Backend Engineer", "link": ""},
            {"name": "OpenHR API", "description": "Open-source HR management REST API used by 12 companies in East Africa.", "technologies": ["Python", "Flask", "PostgreSQL"], "role": "Creator & Maintainer", "link": "https://github.com/aline-uwase/openhr"},
        ],
        "availability_status": "available",
        "availability_type": "full-time",
        "linkedin": "https://linkedin.com/in/aline-uwase",
        "github": "https://github.com/aline-uwase",
        "portfolio_url": "",
        "project_count": 3,
    },
    {
        "job_index": 0,
        "full_name": "Eric Mugisha",
        "email": "eric.mugisha@example.rw",
        "phone": "+250 788 100 002",
        "location": "Kigali, Rwanda",
        "headline": "Backend Engineer · Flask · PostgreSQL · 4 yrs",
        "bio": "Practical engineer who ships working software quickly. Strong in Python backend systems and database design. Currently exploring cloud-native architecture.",
        "years_experience": 4.0,
        "education": "BSc Software Engineering, Carnegie Mellon University Africa",
        "education_level": "bachelors",
        "structured_skills": [
            {"name": "Python",      "level": "Advanced",      "yearsOfExperience": 4},
            {"name": "Flask",       "level": "Intermediate",  "yearsOfExperience": 2},
            {"name": "PostgreSQL",  "level": "Advanced",      "yearsOfExperience": 4},
            {"name": "Docker",      "level": "Intermediate",  "yearsOfExperience": 2},
            {"name": "REST APIs",   "level": "Advanced",      "yearsOfExperience": 4},
        ],
        "languages_data": [
            {"name": "Kinyarwanda", "proficiency": "native"},
            {"name": "English",     "proficiency": "fluent"},
        ],
        "structured_experience": [
            {
                "company": "MTN Rwanda",
                "role": "Backend Engineer",
                "startDate": "2020-07",
                "endDate": None,
                "isCurrent": True,
                "description": "Maintained and extended MoMo payment API, added webhook notification system, improved test coverage from 40% to 85%.",
                "technologies": ["Python", "Flask", "PostgreSQL", "Docker"],
            },
        ],
        "structured_education": [
            {"institution": "Carnegie Mellon University Africa", "degree": "BSc", "field": "Software Engineering", "startYear": 2016, "endYear": 2020},
        ],
        "certifications_data": [],
        "structured_projects": [
            {"name": "MoMo Webhook Service", "description": "Reliable webhook delivery system for mobile payment events with retry logic and dead-letter queue.", "technologies": ["Python", "Flask", "Redis", "PostgreSQL"], "role": "Backend Engineer", "link": ""},
            {"name": "Budget Tracker CLI", "description": "Personal finance tracking tool used by 200+ developers in the local community.", "technologies": ["Python", "SQLite"], "role": "Creator", "link": "https://github.com/eric-mugisha/budget-cli"},
        ],
        "availability_status": "open",
        "availability_type": "full-time",
        "linkedin": "https://linkedin.com/in/eric-mugisha",
        "github": "https://github.com/eric-mugisha",
        "portfolio_url": "",
        "project_count": 2,
    },
    {
        "job_index": 0,
        "full_name": "Jean Bosco Habimana",
        "email": "jbhabimana@example.rw",
        "phone": "+250 788 100 005",
        "location": "Kigali, Rwanda",
        "headline": "Full-Stack Engineer · Node.js & Python · 5 yrs",
        "bio": "Cross-functional engineer comfortable from React to Python backends. Passionate about performance and code that lasts.",
        "years_experience": 5.0,
        "education": "MSc Computer Science, University of Cape Town",
        "education_level": "masters",
        "structured_skills": [
            {"name": "Python",      "level": "Advanced",      "yearsOfExperience": 4},
            {"name": "Flask",       "level": "Advanced",      "yearsOfExperience": 3},
            {"name": "PostgreSQL",  "level": "Advanced",      "yearsOfExperience": 5},
            {"name": "Docker",      "level": "Expert",        "yearsOfExperience": 4},
            {"name": "REST APIs",   "level": "Expert",        "yearsOfExperience": 5},
            {"name": "Node.js",     "level": "Advanced",      "yearsOfExperience": 3},
        ],
        "languages_data": [
            {"name": "Kinyarwanda", "proficiency": "native"},
            {"name": "English",     "proficiency": "fluent"},
            {"name": "French",      "proficiency": "fluent"},
        ],
        "structured_experience": [
            {
                "company": "Kasha",
                "role": "Senior Software Engineer",
                "startDate": "2022-01",
                "endDate": None,
                "isCurrent": True,
                "description": "Led backend rewrite from monolith to microservices. Reduced infrastructure cost by 35%.",
                "technologies": ["Python", "Flask", "PostgreSQL", "Docker", "Kubernetes"],
            },
        ],
        "structured_education": [
            {"institution": "University of Cape Town", "degree": "MSc", "field": "Computer Science", "startYear": 2018, "endYear": 2020},
            {"institution": "University of Rwanda", "degree": "BSc", "field": "Computer Science", "startYear": 2014, "endYear": 2018},
        ],
        "certifications_data": [
            {"name": "Certified Kubernetes Administrator", "issuer": "CNCF", "date": "2023-06"},
        ],
        "structured_projects": [
            {"name": "Kasha Microservices Platform", "description": "Decomposed legacy monolith into 8 independently deployable microservices serving 150K users.", "technologies": ["Python", "Flask", "Docker", "PostgreSQL"], "role": "Lead Architect", "link": ""},
            {"name": "RwandaJobs API", "description": "Public REST API for the Rwandan job market, used by 3 external apps.", "technologies": ["Python", "Flask", "PostgreSQL"], "role": "Creator", "link": "https://github.com/jbhabimana/rwandajobs-api"},
            {"name": "DataSync ETL", "description": "Real-time ETL pipeline synchronising data across 5 internal services.", "technologies": ["Python", "PostgreSQL", "Redis"], "role": "Backend Lead", "link": ""},
        ],
        "availability_status": "open",
        "availability_type": "full-time",
        "linkedin": "https://linkedin.com/in/jean-bosco-habimana",
        "github": "https://github.com/jbhabimana",
        "portfolio_url": "https://jbhabimana.dev",
        "project_count": 3,
    },
    {
        "job_index": 0,
        "full_name": "Grace Umutoni",
        "email": "grace.umutoni@example.rw",
        "phone": "+250 788 100 008",
        "location": "Kigali, Rwanda",
        "headline": "Backend Engineer · Python · 2 yrs",
        "bio": "Junior-to-mid engineer with strong Python foundations. Fast learner with a track record of shipping under deadlines.",
        "years_experience": 2.0,
        "education": "BSc Information Technology, AUCA",
        "education_level": "bachelors",
        "structured_skills": [
            {"name": "Python",      "level": "Intermediate",  "yearsOfExperience": 2},
            {"name": "Flask",       "level": "Beginner",      "yearsOfExperience": 1},
            {"name": "PostgreSQL",  "level": "Intermediate",  "yearsOfExperience": 2},
            {"name": "REST APIs",   "level": "Intermediate",  "yearsOfExperience": 2},
        ],
        "languages_data": [
            {"name": "Kinyarwanda", "proficiency": "native"},
            {"name": "English",     "proficiency": "professional"},
        ],
        "structured_experience": [
            {
                "company": "Irembo",
                "role": "Junior Backend Engineer",
                "startDate": "2023-01",
                "endDate": None,
                "isCurrent": True,
                "description": "Contributed to citizen-services API, fixed critical bugs in production, wrote integration tests.",
                "technologies": ["Python", "PostgreSQL", "REST APIs"],
            },
        ],
        "structured_education": [
            {"institution": "AUCA", "degree": "BSc", "field": "Information Technology", "startYear": 2019, "endYear": 2023},
        ],
        "certifications_data": [],
        "structured_projects": [
            {"name": "Irembo Services Portal", "description": "Government citizen-services web portal — contributed API modules.", "technologies": ["Python", "PostgreSQL"], "role": "Junior Backend Engineer", "link": ""},
        ],
        "availability_status": "available",
        "availability_type": "full-time",
        "linkedin": "https://linkedin.com/in/grace-umutoni",
        "github": "https://github.com/grace-umutoni",
        "portfolio_url": "",
        "project_count": 1,
    },

    # ── Job 1 applicants — Data Scientist ───────────────────────────────────
    {
        "job_index": 1,
        "full_name": "Diane Mukamana",
        "email": "diane.mukamana@example.rw",
        "phone": "+250 788 100 004",
        "location": "Kigali, Rwanda",
        "headline": "Data Scientist · ML & Fraud Analytics · 5 yrs",
        "bio": "Experienced data scientist specializing in financial ML and fraud detection. Published research on mobile-money risk scoring.",
        "years_experience": 5.0,
        "education": "MSc Data Science, African Institute for Mathematical Sciences",
        "education_level": "masters",
        "structured_skills": [
            {"name": "Python",          "level": "Expert",       "yearsOfExperience": 5},
            {"name": "Pandas",          "level": "Expert",       "yearsOfExperience": 5},
            {"name": "Machine Learning","level": "Expert",       "yearsOfExperience": 4},
            {"name": "SQL",             "level": "Advanced",     "yearsOfExperience": 5},
            {"name": "Flask",           "level": "Intermediate", "yearsOfExperience": 2},
            {"name": "scikit-learn",    "level": "Expert",       "yearsOfExperience": 4},
        ],
        "languages_data": [
            {"name": "Kinyarwanda", "proficiency": "native"},
            {"name": "English",     "proficiency": "fluent"},
            {"name": "French",      "proficiency": "fluent"},
        ],
        "structured_experience": [
            {
                "company": "Bank of Kigali",
                "role": "Senior Data Scientist",
                "startDate": "2021-04",
                "endDate": None,
                "isCurrent": True,
                "description": "Built credit risk scoring models reducing loan default rates by 22%. Led a team of 2 data analysts.",
                "technologies": ["Python", "Pandas", "scikit-learn", "SQL", "Flask"],
            },
            {
                "company": "GSMA Mobile for Development",
                "role": "Data Analyst",
                "startDate": "2019-01",
                "endDate": "2021-03",
                "isCurrent": False,
                "description": "Analysed mobile-money transaction data across 8 African markets. Delivered quarterly risk reports.",
                "technologies": ["Python", "Pandas", "SQL"],
            },
        ],
        "structured_education": [
            {"institution": "AIMS Rwanda", "degree": "MSc", "field": "Data Science", "startYear": 2017, "endYear": 2019},
            {"institution": "University of Rwanda", "degree": "BSc", "field": "Mathematics", "startYear": 2013, "endYear": 2017},
        ],
        "certifications_data": [
            {"name": "TensorFlow Developer Certificate", "issuer": "Google", "date": "2022-09"},
            {"name": "IBM Data Science Professional",    "issuer": "IBM",    "date": "2021-02"},
        ],
        "structured_projects": [
            {"name": "BK Credit Scorer", "description": "ML model for credit risk scoring deployed in Bank of Kigali's loan approval pipeline.", "technologies": ["Python", "scikit-learn", "Pandas", "Flask"], "role": "Lead Data Scientist", "link": ""},
            {"name": "MoMo Fraud Detector", "description": "Real-time fraud detection model for mobile-money with 94% precision.", "technologies": ["Python", "Pandas", "scikit-learn", "SQL"], "role": "Data Scientist", "link": "https://github.com/diane-mukamana/momo-fraud"},
            {"name": "African Mobile Money Dashboard", "description": "Interactive Tableau dashboard tracking mobile-money KPIs across 8 African markets.", "technologies": ["Python", "Pandas", "Tableau"], "role": "Creator", "link": ""},
        ],
        "availability_status": "open",
        "availability_type": "full-time",
        "linkedin": "https://linkedin.com/in/diane-mukamana",
        "github": "https://github.com/diane-mukamana",
        "portfolio_url": "https://diane-mukamana.github.io",
        "project_count": 3,
    },

    # ── Job 2 applicants — Frontend Developer ───────────────────────────────
    {
        "job_index": 2,
        "full_name": "Patrick Niyonsaba",
        "email": "p.niyonsaba@example.rw",
        "phone": "+250 788 100 003",
        "location": "Kigali, Rwanda",
        "headline": "Frontend Engineer · React & TypeScript · 4 yrs",
        "bio": "Product-minded frontend engineer who obsesses over user experience. Strong in React, TypeScript, and modern CSS. Contributor to open-source design systems.",
        "years_experience": 4.0,
        "education": "BSc Computer Science, University of Rwanda",
        "education_level": "bachelors",
        "structured_skills": [
            {"name": "JavaScript", "level": "Expert",        "yearsOfExperience": 4},
            {"name": "React",      "level": "Expert",        "yearsOfExperience": 4},
            {"name": "TypeScript", "level": "Advanced",      "yearsOfExperience": 3},
            {"name": "Node.js",    "level": "Advanced",      "yearsOfExperience": 3},
            {"name": "CSS",        "level": "Expert",        "yearsOfExperience": 4},
            {"name": "HTML",       "level": "Expert",        "yearsOfExperience": 4},
            {"name": "Next.js",    "level": "Advanced",      "yearsOfExperience": 2},
        ],
        "languages_data": [
            {"name": "Kinyarwanda", "proficiency": "native"},
            {"name": "English",     "proficiency": "fluent"},
        ],
        "structured_experience": [
            {
                "company": "Zipline Rwanda",
                "role": "Frontend Engineer",
                "startDate": "2021-08",
                "endDate": None,
                "isCurrent": True,
                "description": "Built ops dashboard used by 200+ operators to coordinate drone deliveries. Improved dashboard load time by 60% via code splitting.",
                "technologies": ["React", "TypeScript", "Node.js", "CSS"],
            },
            {
                "company": "Klab Rwanda",
                "role": "Junior Frontend Developer",
                "startDate": "2020-01",
                "endDate": "2021-07",
                "isCurrent": False,
                "description": "Developed responsive UIs for 4 client projects, mentored 2 bootcamp students.",
                "technologies": ["JavaScript", "React", "HTML", "CSS"],
            },
        ],
        "structured_education": [
            {"institution": "University of Rwanda", "degree": "BSc", "field": "Computer Science", "startYear": 2016, "endYear": 2020},
        ],
        "certifications_data": [
            {"name": "Meta Frontend Developer Professional Certificate", "issuer": "Meta", "date": "2022-03"},
        ],
        "structured_projects": [
            {"name": "Zipline Ops Dashboard", "description": "React dashboard used by 200+ drone operations staff, with real-time flight tracking.", "technologies": ["React", "TypeScript", "CSS", "Node.js"], "role": "Lead Frontend Engineer", "link": ""},
            {"name": "RwandaDesign UI Kit", "description": "Open-source React component library with 40+ components, used by 8 Rwanda-based startups.", "technologies": ["React", "TypeScript", "CSS"], "role": "Creator", "link": "https://github.com/pniyonsaba/rwanda-design"},
            {"name": "AfriLearn LMS", "description": "Learning management system frontend serving 5,000+ students.", "technologies": ["Next.js", "TypeScript", "Tailwind CSS"], "role": "Frontend Lead", "link": ""},
        ],
        "availability_status": "open",
        "availability_type": "full-time",
        "linkedin": "https://linkedin.com/in/patrick-niyonsaba",
        "github": "https://github.com/pniyonsaba",
        "portfolio_url": "https://pniyonsaba.dev",
        "project_count": 3,
    },
    {
        "job_index": 2,
        "full_name": "Kevin Ndayisaba",
        "email": "k.ndayisaba@example.rw",
        "phone": "+250 788 100 007",
        "location": "Remote",
        "headline": "Frontend Developer · React · 3 yrs",
        "bio": "Reliable frontend engineer with a solid React and CSS background. Comfortable shipping production features end-to-end in small teams.",
        "years_experience": 3.0,
        "education": "BSc Information Technology, INES-Ruhengeri",
        "education_level": "bachelors",
        "structured_skills": [
            {"name": "JavaScript", "level": "Advanced",     "yearsOfExperience": 3},
            {"name": "React",      "level": "Advanced",     "yearsOfExperience": 3},
            {"name": "CSS",        "level": "Advanced",     "yearsOfExperience": 3},
            {"name": "HTML",       "level": "Advanced",     "yearsOfExperience": 3},
            {"name": "Node.js",    "level": "Intermediate", "yearsOfExperience": 1},
        ],
        "languages_data": [
            {"name": "Kinyarwanda", "proficiency": "native"},
            {"name": "English",     "proficiency": "professional"},
        ],
        "structured_experience": [
            {
                "company": "Sauti ya Mteja",
                "role": "Frontend Developer",
                "startDate": "2022-03",
                "endDate": None,
                "isCurrent": True,
                "description": "Built customer feedback UI for East African SMEs. Implemented multilingual support for 3 languages.",
                "technologies": ["React", "JavaScript", "CSS"],
            },
        ],
        "structured_education": [
            {"institution": "INES-Ruhengeri", "degree": "BSc", "field": "Information Technology", "startYear": 2018, "endYear": 2022},
        ],
        "certifications_data": [],
        "structured_projects": [
            {"name": "Sauti Feedback Widget", "description": "Embeddable customer feedback widget with multilingual support.", "technologies": ["React", "JavaScript", "CSS"], "role": "Developer", "link": ""},
            {"name": "Portfolio Generator", "description": "Template-based developer portfolio generator built with React.", "technologies": ["React", "CSS"], "role": "Creator", "link": "https://github.com/kndayisaba/portfolio-gen"},
        ],
        "availability_status": "available",
        "availability_type": "full-time",
        "linkedin": "https://linkedin.com/in/kevin-ndayisaba",
        "github": "https://github.com/kndayisaba",
        "portfolio_url": "",
        "project_count": 2,
    },

    # ── Job 3 applicants — DevOps Engineer ──────────────────────────────────
    {
        "job_index": 3,
        "full_name": "Eric Tuyishime",
        "email": "e.tuyishime@example.rw",
        "phone": "+250 788 100 009",
        "location": "Kigali, Rwanda",
        "headline": "DevOps Engineer · Kubernetes & GCP · 6 yrs",
        "bio": "Platform engineer with deep experience in cloud-native infrastructure, CI/CD, and SRE practices. Built and operated systems serving millions of users across Africa.",
        "years_experience": 6.0,
        "education": "BSc Computer Engineering, University of Rwanda",
        "education_level": "bachelors",
        "structured_skills": [
            {"name": "Docker",      "level": "Expert",       "yearsOfExperience": 6},
            {"name": "Kubernetes",  "level": "Expert",       "yearsOfExperience": 5},
            {"name": "GCP",         "level": "Expert",       "yearsOfExperience": 5},
            {"name": "Linux",       "level": "Expert",       "yearsOfExperience": 6},
            {"name": "Python",      "level": "Advanced",     "yearsOfExperience": 4},
            {"name": "Terraform",   "level": "Advanced",     "yearsOfExperience": 4},
            {"name": "CI/CD",       "level": "Expert",       "yearsOfExperience": 5},
        ],
        "languages_data": [
            {"name": "Kinyarwanda", "proficiency": "native"},
            {"name": "English",     "proficiency": "fluent"},
        ],
        "structured_experience": [
            {
                "company": "mPharma Africa",
                "role": "Senior Platform Engineer",
                "startDate": "2020-09",
                "endDate": None,
                "isCurrent": True,
                "description": "Architected GCP infrastructure supporting operations in 8 African countries. Achieved 99.98% uptime SLA.",
                "technologies": ["GCP", "Kubernetes", "Terraform", "Docker", "Python"],
            },
            {
                "company": "Rwanda Development Board",
                "role": "DevOps Engineer",
                "startDate": "2018-01",
                "endDate": "2020-08",
                "isCurrent": False,
                "description": "Built CI/CD pipelines for 12 government digital services. Implemented monitoring and alerting infrastructure.",
                "technologies": ["Docker", "Linux", "Kubernetes", "GCP"],
            },
        ],
        "structured_education": [
            {"institution": "University of Rwanda", "degree": "BSc", "field": "Computer Engineering", "startYear": 2014, "endYear": 2018},
        ],
        "certifications_data": [
            {"name": "Google Professional Cloud Architect",    "issuer": "Google Cloud", "date": "2021-11"},
            {"name": "Certified Kubernetes Administrator",     "issuer": "CNCF",         "date": "2022-04"},
            {"name": "HashiCorp Certified Terraform Associate","issuer": "HashiCorp",    "date": "2022-09"},
        ],
        "structured_projects": [
            {"name": "mPharma Africa Infra", "description": "Multi-region GCP infrastructure serving pharmacy operations in 8 African countries with 99.98% uptime.", "technologies": ["GCP", "Kubernetes", "Terraform", "Docker"], "role": "Lead Platform Engineer", "link": ""},
            {"name": "RDB CI/CD Platform", "description": "Standardized CI/CD platform used by 12 government digital services.", "technologies": ["Docker", "Kubernetes", "Linux", "Python"], "role": "DevOps Engineer", "link": ""},
            {"name": "Uptime Monitor", "description": "Open-source lightweight uptime monitoring tool used by 50+ startups.", "technologies": ["Python", "Docker"], "role": "Creator", "link": "https://github.com/etuyishime/uptime-monitor"},
        ],
        "availability_status": "open",
        "availability_type": "contract",
        "linkedin": "https://linkedin.com/in/eric-tuyishime",
        "github": "https://github.com/etuyishime",
        "portfolio_url": "",
        "project_count": 3,
    },
    {
        "job_index": 3,
        "full_name": "Sarah Ingabire",
        "email": "s.ingabire@example.rw",
        "phone": "+250 788 100 006",
        "location": "Remote",
        "headline": "Platform / Infrastructure Engineer · Docker & Python · 5 yrs",
        "bio": "Infrastructure engineer who bridges software development and operations. Strong in containerization, automation, and cloud cost optimization.",
        "years_experience": 5.0,
        "education": "BSc Software Engineering, Carnegie Mellon University Africa",
        "education_level": "bachelors",
        "structured_skills": [
            {"name": "Docker",      "level": "Expert",       "yearsOfExperience": 5},
            {"name": "Kubernetes",  "level": "Advanced",     "yearsOfExperience": 3},
            {"name": "GCP",         "level": "Intermediate", "yearsOfExperience": 2},
            {"name": "Linux",       "level": "Expert",       "yearsOfExperience": 5},
            {"name": "Python",      "level": "Expert",       "yearsOfExperience": 5},
            {"name": "Terraform",   "level": "Intermediate", "yearsOfExperience": 2},
        ],
        "languages_data": [
            {"name": "Kinyarwanda", "proficiency": "native"},
            {"name": "English",     "proficiency": "fluent"},
            {"name": "French",      "proficiency": "professional"},
        ],
        "structured_experience": [
            {
                "company": "Ericsson (Rwanda Office)",
                "role": "Infrastructure Engineer",
                "startDate": "2020-02",
                "endDate": None,
                "isCurrent": True,
                "description": "Managed containerized telecom network functions, automated deployment with Ansible and Terraform, reduced deployment time by 70%.",
                "technologies": ["Docker", "Kubernetes", "Linux", "Python", "Terraform"],
            },
        ],
        "structured_education": [
            {"institution": "Carnegie Mellon University Africa", "degree": "BSc", "field": "Software Engineering", "startYear": 2016, "endYear": 2020},
        ],
        "certifications_data": [
            {"name": "AWS Certified SysOps Administrator", "issuer": "Amazon Web Services", "date": "2022-07"},
        ],
        "structured_projects": [
            {"name": "Telecom Deployment Automation", "description": "Ansible + Terraform automation reducing telecom function deployment from 4 hours to 12 minutes.", "technologies": ["Python", "Terraform", "Docker", "Linux"], "role": "Infrastructure Engineer", "link": ""},
            {"name": "Container Health Monitor", "description": "Lightweight Docker container health monitoring dashboard.", "technologies": ["Python", "Docker"], "role": "Creator", "link": "https://github.com/singabire/container-monitor"},
        ],
        "availability_status": "open",
        "availability_type": "full-time",
        "linkedin": "https://linkedin.com/in/sarah-ingabire",
        "github": "https://github.com/singabire",
        "portfolio_url": "",
        "project_count": 2,
    },
]


def seed(recruiter_email=None):
    from models import Recruiter

    app = create_app()
    with app.app_context():
        if Job.query.count() > 0:
            print("[seed] Database already has data — skipping. Delete instance/mpact.db to re-seed.")
            return

        # Resolve recruiter
        recruiter = None
        if recruiter_email:
            recruiter = Recruiter.query.filter_by(email=recruiter_email.strip().lower()).first()
            if not recruiter:
                print(f"[seed] ERROR: No recruiter found with email '{recruiter_email}'. Register first.")
                return
        else:
            recruiter = Recruiter.query.first()
            if not recruiter:
                print("[seed] ERROR: No recruiter accounts exist yet.")
                print("       Register a recruiter account at /recruiter/register, verify it, then re-run:")
                print("       python seed.py your@email.com")
                return

        print(f"[seed] Assigning all jobs to recruiter: {recruiter.name} ({recruiter.email})")

        jobs = []
        for jd in DEMO_JOBS:
            j = Job(**jd, is_published=True, recruiter_id=recruiter.id)
            db.session.add(j)
            jobs.append(j)
        db.session.flush()

        for profile in DEMO_APPLICANTS:
            idx = profile["job_index"]
            if idx >= len(jobs):
                continue

            flat_skills = ", ".join(
                s["name"] for s in profile.get("structured_skills", [])
            )

            a = Applicant(
                job_id=jobs[idx].id,
                full_name=profile["full_name"],
                email=profile["email"],
                phone=profile["phone"],
                location=profile["location"],
                headline=profile.get("headline"),
                bio=profile.get("bio"),
                skills=flat_skills,
                years_experience=profile.get("years_experience", 0),
                education=profile.get("education", ""),
                education_level=profile.get("education_level", "bachelors"),
                project_count=profile.get("project_count", 0),
                structured_skills=json.dumps(profile["structured_skills"]),
                languages_data=json.dumps(profile["languages_data"]),
                structured_experience=json.dumps(profile["structured_experience"]),
                structured_education=json.dumps(profile["structured_education"]),
                certifications_data=json.dumps(profile["certifications_data"]),
                structured_projects=json.dumps(profile["structured_projects"]),
                availability_status=profile.get("availability_status"),
                availability_type=profile.get("availability_type"),
                linkedin=profile.get("linkedin"),
                github=profile.get("github"),
                portfolio_url=profile.get("portfolio_url"),
                source="seed",
                status="new",
            )
            db.session.add(a)

        db.session.commit()
        total_applicants = Applicant.query.count()
        print(f"[seed] Created {len(jobs)} jobs and {total_applicants} schema-compliant applicant records.")


if __name__ == "__main__":
    import sys
    email_arg = sys.argv[1] if len(sys.argv) > 1 else None
    seed(email_arg)
