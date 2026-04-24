"""Deterministic weighted scoring. Pairs with Gemini for qualitative analysis."""
import re

SKILL_LEVEL_WEIGHTS = {
    "expert":       1.00,
    "advanced":     0.85,
    "intermediate": 0.65,
    "beginner":     0.35,
}

EDUCATION_LEVELS = {
    "phd": 100,
    "masters": 85,
    "bachelors": 70,
    "diploma": 50,
    "highschool": 30,
    "none": 10,
}

REQUIRED_LEVEL_THRESHOLD = {
    "phd": "phd",
    "masters": "masters",
    "bachelors": "bachelors",
    "diploma": "diploma",
    "any": "none",
}


def _normalize(text):
    return (text or "").strip().lower()


def _tokenize(skill_text):
    """Tokenize a skill string into a set of significant words."""
    return {w for w in re.split(r"[\s/+.,\-]+", skill_text.lower()) if len(w) > 1}


def score_skills(applicant_skills, required_skills):
    if not required_skills:
        return 100.0 if applicant_skills else 50.0
    req = [_normalize(s) for s in required_skills if s]
    have = [_normalize(s) for s in applicant_skills if s]
    if not req:
        return 50.0

    matched = 0
    for r in req:
        r_tokens = _tokenize(r)
        for h in have:
            h_tokens = _tokenize(h)
            # Exact normalized match OR meaningful token overlap (avoids "Go" matching "PostgreSQL")
            if r == h or (r_tokens and h_tokens and len(r_tokens & h_tokens) >= max(1, min(len(r_tokens), len(h_tokens)) // 2)):
                matched += 1
                break
    return round((matched / len(req)) * 100, 1)


def score_experience(years, min_required):
    years = years or 0
    min_required = min_required or 0
    if min_required == 0:
        return min(100.0, 60 + years * 8)
    ratio = years / min_required
    if ratio >= 1.5:
        return 100.0
    if ratio >= 1.0:
        return 85.0 + (ratio - 1.0) * 30
    return round(max(20.0, ratio * 80), 1)


def score_education(level, required):
    level = _normalize(level) or "none"
    required = _normalize(required) or "any"
    base = EDUCATION_LEVELS.get(level, 30)
    needed_key = REQUIRED_LEVEL_THRESHOLD.get(required, "none")
    needed = EDUCATION_LEVELS.get(needed_key, 10)
    if base >= needed:
        return float(base)
    return round(base * 0.6, 1)


def score_skills_structured(structured_skills, required_skills):
    """Score skills using structured {name, level, yearsOfExperience} entries.
    Expert match = 1.0, Advanced = 0.85, Intermediate = 0.65, Beginner = 0.35.
    """
    if not required_skills:
        return 100.0 if structured_skills else 50.0
    req = [_normalize(s) for s in required_skills if s]
    if not req:
        return 50.0
    matched_weight = 0.0
    for r in req:
        r_tokens = _tokenize(r)
        for entry in structured_skills:
            h = _normalize(entry.get("name", ""))
            if not h:
                continue
            h_tokens = _tokenize(h)
            level = _normalize(entry.get("level", "intermediate"))
            weight = SKILL_LEVEL_WEIGHTS.get(level, 0.65)
            if r == h or (r_tokens and h_tokens and len(r_tokens & h_tokens) >= max(1, min(len(r_tokens), len(h_tokens)) // 2)):
                matched_weight += weight
                break
    return round((matched_weight / len(req)) * 100, 1)


def score_projects(project_count):
    if not project_count:
        return 30.0
    if project_count >= 5:
        return 100.0
    return round(30 + project_count * 14, 1)


def compute_weighted_score(applicant, job):
    if applicant.structured_skills_list:
        s = score_skills_structured(applicant.structured_skills_list, job.skills_list)
    else:
        s = score_skills(applicant.skills_list, job.skills_list)
    e = score_experience(applicant.years_experience, job.min_years_experience)
    ed = score_education(applicant.education_level, job.required_education)
    p = score_projects(applicant.project_count)

    total_weight = (
        job.weight_skills + job.weight_experience + job.weight_education + job.weight_projects
    ) or 100

    weighted = (
        s * job.weight_skills
        + e * job.weight_experience
        + ed * job.weight_education
        + p * job.weight_projects
    ) / total_weight

    return {
        "skills_score": s,
        "experience_score": e,
        "education_score": ed,
        "projects_score": p,
        "weighted_score": round(weighted, 1),
    }
