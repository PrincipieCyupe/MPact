from datetime import datetime
import json
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


class Recruiter(db.Model):
    __tablename__ = "recruiters"

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(200), nullable=False)
    email      = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    company    = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    is_verified       = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), unique=True, nullable=True)
    token_expires_at  = db.Column(db.DateTime, nullable=True)

    jobs = db.relationship("Job", backref="recruiter", lazy="dynamic")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def initials(self):
        parts = [p for p in (self.name or "").split() if p]
        if not parts:
            return "?"
        return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else parts[0][1])).upper()

    @property
    def first_name(self):
        return (self.name or "").split()[0] if self.name else "Recruiter"


class JobField(db.Model):
    """Custom question a recruiter adds to a specific job's application form."""
    __tablename__ = "job_fields"

    id         = db.Column(db.Integer, primary_key=True)
    job_id     = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    label      = db.Column(db.String(300), nullable=False)
    field_type = db.Column(db.String(40), default="text")   # text | textarea | yesno | select
    options    = db.Column(db.Text)                          # JSON list, only for select
    required   = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)

    @property
    def options_list(self):
        try:
            return json.loads(self.options) if self.options else []
        except Exception:
            return []

    def to_dict(self):
        return {
            "id":       self.id,
            "label":    self.label,
            "type":     self.field_type,
            "options":  self.options_list,
            "required": self.required,
        }


class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    recruiter_id = db.Column(db.Integer, db.ForeignKey("recruiters.id"), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(120))
    location = db.Column(db.String(120))
    employment_type = db.Column(db.String(60))  # Full-time, Contract, etc
    seniority = db.Column(db.String(60))
    description = db.Column(db.Text)
    required_skills = db.Column(db.Text)  # comma-separated
    min_years_experience = db.Column(db.Integer, default=0)
    required_education = db.Column(db.String(120))

    # scoring weights (sum to 100)
    weight_skills = db.Column(db.Integer, default=40)
    weight_experience = db.Column(db.Integer, default=30)
    weight_education = db.Column(db.Integer, default=15)
    weight_projects = db.Column(db.Integer, default=15)

    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applicants = db.relationship(
        "Applicant", backref="job", cascade="all, delete-orphan", lazy="dynamic"
    )
    custom_fields = db.relationship(
        "JobField", backref="job", cascade="all, delete-orphan",
        order_by="JobField.sort_order", lazy=True
    )

    @property
    def skills_list(self):
        if not self.required_skills:
            return []
        return [s.strip() for s in self.required_skills.split(",") if s.strip()]

    @property
    def applicant_count(self):
        return self.applicants.count()

    @property
    def screened_count(self):
        return self.applicants.filter(Applicant.final_score.isnot(None)).count()

    @property
    def shortlist_count(self):
        return self.applicants.filter(
            Applicant.ai_recommendation.in_(["strong_fit", "fit"])
        ).count()

    @property
    def short_location(self):
        return self.location or "Remote"

    @property
    def meta_line(self):
        parts = [p for p in [self.employment_type, self.seniority, self.short_location] if p]
        return " · ".join(parts)


class Applicant(db.Model):
    __tablename__ = "applicants"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)

    full_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200))
    phone = db.Column(db.String(60))
    location = db.Column(db.String(120))

    skills = db.Column(db.Text)              # comma-separated
    years_experience = db.Column(db.Float, default=0)
    education = db.Column(db.String(200))
    education_level = db.Column(db.String(60))  # phd, masters, bachelors, diploma, none
    projects = db.Column(db.Text)            # free text
    project_count = db.Column(db.Integer, default=0)

    resume_filename = db.Column(db.String(300))  # stored under instance/uploads
    resume_text = db.Column(db.Text)
    custom_answers = db.Column(db.Text)  # JSON: {"field_id": "answer", ...}
    source = db.Column(db.String(40), default="web")  # web | seed

    status = db.Column(db.String(40), default="new")  # new | reviewed | shortlisted | interview | rejected

    # screening output
    skills_score = db.Column(db.Float)
    experience_score = db.Column(db.Float)
    education_score = db.Column(db.Float)
    projects_score = db.Column(db.Float)
    weighted_score = db.Column(db.Float)
    ai_score = db.Column(db.Float)
    final_score = db.Column(db.Float)

    ai_strengths = db.Column(db.Text)        # JSON list
    ai_gaps = db.Column(db.Text)             # JSON list
    ai_recommendation = db.Column(db.String(40))  # strong_fit | fit | maybe | not_fit
    ai_reasoning = db.Column(db.Text)
    bias_flag = db.Column(db.Boolean, default=False)
    bias_notes = db.Column(db.Text)
    recruiter_notes = db.Column(db.Text)

    # Umurava Talent Profile Schema
    headline = db.Column(db.String(300))
    bio = db.Column(db.Text)
    structured_skills = db.Column(db.Text)      # JSON: [{name, level, yearsOfExperience}]
    languages_data = db.Column(db.Text)         # JSON: [{language, proficiency}]
    structured_experience = db.Column(db.Text)  # JSON: [{company, title, startDate, endDate, isCurrent, description, skills[]}]
    structured_education = db.Column(db.Text)   # JSON: [{institution, degree, field, startYear, endYear}]
    certifications_data = db.Column(db.Text)    # JSON: [{name, issuer, date, url}]
    structured_projects = db.Column(db.Text)    # JSON: [{name, description, url, skills[], isFeatured}]
    availability_status = db.Column(db.String(40))   # available | open | not-available
    availability_type = db.Column(db.String(40))     # full-time | part-time | contract | freelance
    linkedin = db.Column(db.String(300))
    github = db.Column(db.String(300))
    portfolio_url = db.Column(db.String(300))

    screened_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def custom_answers_dict(self):
        try:
            return json.loads(self.custom_answers) if self.custom_answers else {}
        except Exception:
            return {}

    @property
    def skills_list(self):
        if self.structured_skills:
            try:
                data = json.loads(self.structured_skills)
                names = [s.get("name", "").strip() for s in data if s.get("name")]
                if names:
                    return names
            except Exception:
                pass
        if not self.skills:
            return []
        return [s.strip() for s in self.skills.split(",") if s.strip()]

    @property
    def structured_skills_list(self):
        try:
            return json.loads(self.structured_skills) if self.structured_skills else []
        except Exception:
            return []

    @property
    def structured_experience_list(self):
        try:
            return json.loads(self.structured_experience) if self.structured_experience else []
        except Exception:
            return []

    @property
    def structured_education_list(self):
        try:
            return json.loads(self.structured_education) if self.structured_education else []
        except Exception:
            return []

    @property
    def certifications_list(self):
        try:
            return json.loads(self.certifications_data) if self.certifications_data else []
        except Exception:
            return []

    @property
    def structured_projects_list(self):
        try:
            return json.loads(self.structured_projects) if self.structured_projects else []
        except Exception:
            return []

    @property
    def languages_list(self):
        try:
            return json.loads(self.languages_data) if self.languages_data else []
        except Exception:
            return []

    @property
    def strengths_list(self):
        try:
            return json.loads(self.ai_strengths) if self.ai_strengths else []
        except Exception:
            return []

    @property
    def gaps_list(self):
        try:
            return json.loads(self.ai_gaps) if self.ai_gaps else []
        except Exception:
            return []

    @property
    def recommendation_label(self):
        return {
            "strong_fit": "Strong fit",
            "fit": "Good fit",
            "maybe": "Maybe",
            "not_fit": "Not a fit",
        }.get(self.ai_recommendation, "Unscreened")

    @property
    def initials(self):
        parts = [p for p in (self.full_name or "").split() if p]
        if not parts:
            return "?"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[-1][0]).upper()

    @property
    def avatar_color(self):
        """Deterministic HSL color from name hash."""
        if not self.full_name:
            return "hsl(240, 60%, 60%)"
        h = int(hashlib.md5(self.full_name.encode("utf-8")).hexdigest(), 16)
        hue = h % 360
        return f"hsl({hue}, 55%, 55%)"

    @property
    def avatar_bg(self):
        if not self.full_name:
            return "hsl(240, 60%, 95%)"
        h = int(hashlib.md5(self.full_name.encode("utf-8")).hexdigest(), 16)
        hue = h % 360
        return f"hsl({hue}, 70%, 94%)"

    @property
    def recommendation_tone(self):
        return {
            "strong_fit": "success",
            "fit": "info",
            "maybe": "warn",
            "not_fit": "danger",
        }.get(self.ai_recommendation, "muted")
