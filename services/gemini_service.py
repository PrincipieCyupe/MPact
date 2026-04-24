"""
Gemini integration — batch evaluation, bias detection, JD extraction.
All candidates for a job are evaluated in ONE API call for speed + hackathon compliance.
"""
import json
import re
import time
from datetime import datetime

from config import Config

_model = None
_model_name = None
BOLD = "\033[1m"
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
RESET = "\033[0m"
DIM = "\033[2m"


def _log(msg, color=RESET):
    ts = datetime.utcnow().strftime("%H:%M:%S")
    print(f"{DIM}[{ts}]{RESET} {color}{msg}{RESET}", flush=True)


def _get_model():
    global _model, _model_name
    if _model is not None and _model_name == Config.GEMINI_MODEL:
        return _model
    if not Config.GEMINI_API_KEY:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=Config.GEMINI_API_KEY)
        _model = genai.GenerativeModel(Config.GEMINI_MODEL)
        _model_name = Config.GEMINI_MODEL
        _log(f"Gemini model ready: {Config.GEMINI_MODEL}", GREEN)
        return _model
    except Exception as exc:
        _log(f"Gemini init failed: {exc}", RED)
        return None


# ──────────────────────────────────────────────────────────────────────────────
# BATCH EVALUATION  (single API call for all candidates)
# ──────────────────────────────────────────────────────────────────────────────

def _build_batch_prompt(job, candidates):
    """Build a single prompt that evaluates ALL candidates using the full Umurava schema."""
    job_block = f"""JOB DETAILS
Title: {job.title}
Seniority: {job.seniority or 'Not specified'}
Required Skills: {', '.join(job.skills_list) or 'Not specified'}
Min Experience: {job.min_years_experience} years
Required Education: {job.required_education or 'Any'}
Description: {(job.description or '')[:1500]}"""

    cand_blocks = []
    for c in candidates:
        block = {"id": c["id"], "name": c["name"]}

        if c.get("headline"):
            block["headline"] = c["headline"]

        # Skills — prefer structured with proficiency levels
        structured_skills = c.get("structured_skills") or []
        if structured_skills:
            block["skills"] = structured_skills
        else:
            block["skills"] = c.get("skills") or "N/A"

        block["years_experience"] = c.get("years_experience") or 0

        # Education — prefer structured timeline
        structured_edu = c.get("structured_education") or []
        if structured_edu:
            block["education"] = structured_edu
        else:
            block["education"] = f"{c.get('education') or 'N/A'} ({c.get('education_level') or 'N/A'})"

        # Experience timeline
        structured_exp = c.get("structured_experience") or []
        if structured_exp:
            block["experience_timeline"] = structured_exp

        # Certifications
        certs = c.get("certifications") or []
        if certs:
            block["certifications"] = certs

        # Projects — prefer structured
        structured_proj = c.get("structured_projects") or []
        if structured_proj:
            block["projects"] = structured_proj
        else:
            block["projects"] = (c.get("projects") or "N/A")[:400]

        # Languages
        langs = c.get("languages") or []
        if langs:
            block["languages"] = langs

        # Availability
        if c.get("availability_status"):
            block["availability"] = {
                "status": c["availability_status"],
                "type": c.get("availability_type") or "",
            }

        # Resume excerpt for candidates who uploaded a PDF
        resume_excerpt = (c.get("resume_text") or "")[:1200]
        if resume_excerpt:
            block["resume_excerpt"] = resume_excerpt

        if c.get("custom_qa"):
            block["application_responses"] = c["custom_qa"]

        cand_blocks.append(block)

    candidates_json = json.dumps(cand_blocks, indent=2)

    return f"""You are a world-class technical recruiter and AI screening specialist. Evaluate ALL candidates below against the job requirements simultaneously.

{job_block}

CANDIDATES TO EVALUATE:
{candidates_json}

INSTRUCTIONS:
- Score each candidate holistically (0-100) using ALL available structured data: skill proficiency levels, experience timeline, education, certifications, projects, availability, and application responses
- When skills have proficiency levels (Expert/Advanced/Intermediate/Beginner), weight Expert and Advanced skills more heavily in your evaluation
- If a candidate has application_responses, factor their answers into the score and cite them in strengths/gaps/reasoning
- Provide 3-5 specific strengths grounded in their actual profile data (cite skill levels, companies, certifications if present)
- Provide 2-4 honest gaps or risks (be constructive, not harsh)
- Give recommendation: "strong_fit" (85+), "fit" (70-84), "maybe" (50-69), "not_fit" (<50)
- Write 2-3 sentence reasoning that references SPECIFIC evidence from their profile
- Flag potential bias: identify if resume contains signals that could introduce unconscious bias (name-based, location-based, institution prestige bias, etc.)

Return ONLY a valid JSON array (no markdown, no commentary):
[
  {{
    "id": <candidate_id>,
    "ai_score": <integer 0-100>,
    "strengths": ["<specific strength 1>", "..."],
    "gaps": ["<specific gap 1>", "..."],
    "recommendation": "strong_fit" | "fit" | "maybe" | "not_fit",
    "reasoning": "<2-3 sentence evidence-based explanation>",
    "bias_flag": true | false,
    "bias_notes": "<brief note if bias_flag is true, else empty string>"
  }},
  ...
]"""


def _build_single_prompt(job, applicant):
    """Fallback single-candidate prompt."""
    return f"""You are an expert technical recruiter. Evaluate this candidate against the job.
Return ONLY valid JSON, no markdown fencing.

JOB
Title: {job.title}
Seniority: {job.seniority or 'N/A'}
Required skills: {', '.join(job.skills_list) or 'N/A'}
Min experience: {job.min_years_experience} years
Required education: {job.required_education or 'Any'}
Description: {(job.description or '')[:1200]}

CANDIDATE
Name: {applicant.full_name}
Skills: {applicant.skills or 'N/A'}
Years experience: {applicant.years_experience}
Education: {applicant.education or 'N/A'} ({applicant.education_level or 'N/A'})
Projects: {(applicant.projects or 'N/A')[:600]}
Resume excerpt: {(applicant.resume_text or '')[:1500]}

Return JSON:
{{
  "ai_score": <integer 0-100>,
  "strengths": [<3-5 bullet strings>],
  "gaps": [<2-4 bullet strings>],
  "recommendation": "strong_fit" | "fit" | "maybe" | "not_fit",
  "reasoning": "<2-3 sentence explanation>",
  "bias_flag": false,
  "bias_notes": ""
}}"""


def _extract_json_array(text):
    """Extract JSON array from response, stripping markdown fencing."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return json.loads(text)


def _extract_json_object(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return json.loads(text)


def _heuristic_fallback_single(job, applicant, weighted_score):
    """Deterministic fallback when Gemini is unavailable."""
    score = int(weighted_score)
    have = {s.lower() for s in applicant.skills_list}
    need = {s.lower() for s in job.skills_list}
    matched = sorted(need & have)
    missing = sorted(need - have)

    strengths = []
    if matched:
        strengths.append(f"Direct experience with {', '.join(matched[:4])}")
    if applicant.years_experience and job.min_years_experience and applicant.years_experience >= job.min_years_experience:
        strengths.append(f"{applicant.years_experience:.0f} years of relevant experience meets the minimum")
    if applicant.project_count and applicant.project_count >= 3:
        strengths.append(f"Solid portfolio with {applicant.project_count} shipped projects")
    if applicant.education_level in ("masters", "phd", "bachelors"):
        strengths.append(f"Formal {applicant.education_level} degree background")
    if not strengths:
        strengths.append("General profile aligns with role description")

    gaps = []
    if missing:
        gaps.append(f"Missing required skills: {', '.join(missing[:4])}")
    if job.min_years_experience and applicant.years_experience < job.min_years_experience:
        gaps.append(f"Experience ({applicant.years_experience:.0f}yr) below the {job.min_years_experience}-year minimum")
    if not gaps:
        gaps.append("No major gaps identified from structured profile")

    if score >= 85:
        rec = "strong_fit"
    elif score >= 70:
        rec = "fit"
    elif score >= 50:
        rec = "maybe"
    else:
        rec = "not_fit"

    return {
        "ai_score": score,
        "strengths": strengths[:5],
        "gaps": gaps[:4],
        "recommendation": rec,
        "reasoning": (
            f"Heuristic analysis: {len(matched)} of {len(need) or 1} required skills matched "
            f"with {applicant.years_experience or 0:.0f} years of experience. "
            f"Configure GEMINI_API_KEY for richer AI analysis."
        ),
        "bias_flag": False,
        "bias_notes": "",
    }


# ──────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ──────────────────────────────────────────────────────────────────────────────

def analyze_batch(job, applicants, weighted_scores):
    """
    Evaluate ALL applicants in a single Gemini API call.
    Returns dict keyed by applicant.id → {ai_score, strengths, gaps, recommendation, reasoning, bias_flag, bias_notes}
    """
    model = _get_model()

    # Build candidate payloads with full Umurava schema fields
    candidates = []
    for a in applicants:
        payload = {
            "id": a.id,
            "name": a.full_name,
            "headline": a.headline or "",
            "skills": a.skills,
            "structured_skills": a.structured_skills_list,
            "years_experience": a.years_experience,
            "education": a.education,
            "education_level": a.education_level,
            "structured_education": a.structured_education_list,
            "structured_experience": a.structured_experience_list,
            "certifications": a.certifications_list,
            "projects": a.projects,
            "structured_projects": a.structured_projects_list,
            "languages": a.languages_list,
            "availability_status": a.availability_status or "",
            "availability_type": a.availability_type or "",
            "resume_text": a.resume_text,
        }
        answers = a.custom_answers_dict
        if answers and a.job.custom_fields:
            payload["custom_qa"] = [
                {"question": f.label, "answer": answers[str(f.id)]}
                for f in a.job.custom_fields
                if answers.get(str(f.id))
            ]
        candidates.append(payload)

    total = len(candidates)
    _log(f"{'━'*60}", CYAN)
    _log(f"  {BOLD}MPACT AI SCREENING  —  {job.title}{RESET}", CYAN)
    _log(f"  Candidates: {total}  |  Model: {Config.GEMINI_MODEL}", CYAN)
    _log(f"{'━'*60}", CYAN)

    # Heuristic fallback dict
    fallback_results = {}
    for a in applicants:
        ws = weighted_scores.get(a.id, 50)
        fallback_results[a.id] = _heuristic_fallback_single(job, a, ws)

    if model is None:
        _log("No Gemini API key — using heuristic fallback for all candidates", YELLOW)
        for a in applicants:
            _log(f"  [{a.id:>3}] {a.full_name:<30} score={fallback_results[a.id]['ai_score']:>3}  {fallback_results[a.id]['recommendation']}", DIM)
        return fallback_results

    # ── BATCH CALL (with retry on 429) ──
    _log(f"Sending batch prompt ({total} candidates) to Gemini...", CYAN)
    t0 = time.time()
    try:
        prompt = _build_batch_prompt(job, candidates)
        _log(f"\n{'─'*60}\n[PROMPT SENT TO GEMINI — {len(prompt)} chars]\n{prompt[:600]}...\n{'─'*60}", DIM)
        resp = None
        for attempt in range(1, 4):  # up to 3 attempts
            try:
                resp = model.generate_content(prompt)
                break
            except Exception as _retry_exc:
                exc_str = str(_retry_exc)
                if "PerDay" in exc_str or "per_day" in exc_str.lower():
                    raise  # daily limit — don't retry, go straight to heuristic
                if "429" in exc_str or "quota" in exc_str.lower():
                    delay_match = re.search(r"seconds:\s*(\d+)", exc_str)
                    wait = min(int(delay_match.group(1)) if delay_match else (attempt * 15), 65)
                    _log(f"Quota hit (attempt {attempt}/3) — waiting {wait}s before retry...", YELLOW)
                    time.sleep(wait)
                    if attempt == 3:
                        raise
                else:
                    raise
        elapsed = time.time() - t0
        _log(f"Gemini responded in {elapsed:.1f}s", GREEN)
        _log(f"\n{'─'*60}\n[RAW GEMINI RESPONSE — {len(resp.text)} chars]\n{resp.text[:800]}...\n{'─'*60}", DIM)

        results_list = _extract_json_array(resp.text)
        results_map = {}
        for item in results_list:
            aid = int(item["id"])
            results_map[aid] = {
                "ai_score": max(0, min(100, int(item.get("ai_score", 50)))),
                "strengths": list(item.get("strengths", []))[:5],
                "gaps": list(item.get("gaps", []))[:4],
                "recommendation": item.get("recommendation", "maybe")
                    if item.get("recommendation") in ("strong_fit", "fit", "maybe", "not_fit")
                    else "maybe",
                "reasoning": str(item.get("reasoning", ""))[:800],
                "bias_flag": bool(item.get("bias_flag", False)),
                "bias_notes": str(item.get("bias_notes", ""))[:300],
            }

        _log(f"\n  {'#':<4} {'Name':<30} {'Score':>5}  {'Match':<12} {'Bias'}", BOLD)
        _log(f"  {'─'*4}  {'─'*30}  {'─'*5}  {'─'*12}  {'─'*4}", DIM)
        for i, a in enumerate(sorted(applicants, key=lambda x: results_map.get(x.id, {}).get("ai_score", 0), reverse=True), 1):
            r = results_map.get(a.id, fallback_results[a.id])
            rec = r["recommendation"]
            col = GREEN if rec == "strong_fit" else (CYAN if rec == "fit" else (YELLOW if rec == "maybe" else RED))
            bias_indicator = f"{YELLOW}⚠ bias{RESET}" if r.get("bias_flag") else f"{GREEN}ok{RESET}"
            _log(f"  {i:<4} {a.full_name:<30} {r['ai_score']:>5}  {col}{rec:<12}{RESET}  {bias_indicator}", "")

        # Fill any missing candidates with fallback
        for a in applicants:
            if a.id not in results_map:
                _log(f"  [WARN] Candidate {a.id} ({a.full_name}) missing from batch response — using fallback", YELLOW)
                results_map[a.id] = fallback_results[a.id]

        strong = sum(1 for r in results_map.values() if r["recommendation"] == "strong_fit")
        fit = sum(1 for r in results_map.values() if r["recommendation"] == "fit")
        maybe = sum(1 for r in results_map.values() if r["recommendation"] == "maybe")
        no = sum(1 for r in results_map.values() if r["recommendation"] == "not_fit")
        bias_count = sum(1 for r in results_map.values() if r.get("bias_flag"))
        _log(f"\n  Summary: {GREEN}Strong={strong}{RESET}  {CYAN}Fit={fit}{RESET}  {YELLOW}Maybe={maybe}{RESET}  {RED}No={no}{RESET}  {YELLOW}BiasFlags={bias_count}{RESET}", "")
        _log(f"{'━'*60}\n", CYAN)
        return results_map

    except Exception as exc:
        elapsed = time.time() - t0
        exc_str = str(exc)
        _log(f"Batch call failed after {elapsed:.1f}s: {exc}", RED)

        # Daily quota exhausted — individual calls will also fail, skip straight to heuristic
        if "PerDay" in exc_str or "per_day" in exc_str.lower():
            _log("Daily quota exhausted — using heuristic for all candidates (get a fresh API key to restore AI)", YELLOW)
            _log(f"{'━'*60}\n", CYAN)
            return fallback_results

        _log("Falling back to individual calls...", YELLOW)

        # Individual fallback calls (only reached on per-minute limits, not daily)
        results_map = {}
        for i, a in enumerate(applicants, 1):
            _log(f"  [{i}/{total}] {a.full_name}...", DIM)
            try:
                single_resp = None
                for _attempt in range(1, 3):
                    try:
                        single_resp = model.generate_content(_build_single_prompt(job, a))
                        break
                    except Exception as _se:
                        se_str = str(_se)
                        if "PerDay" in se_str or "per_day" in se_str.lower():
                            _log(f"  Daily quota hit — stopping individual calls, using heuristic for remaining", YELLOW)
                            raise
                        if ("429" in se_str or "quota" in se_str.lower()) and _attempt == 1:
                            delay_m = re.search(r"seconds:\s*(\d+)", se_str)
                            wait = min(int(delay_m.group(1)) if delay_m else 20, 60)
                            _log(f"  Quota hit for {a.full_name}, waiting {wait}s...", YELLOW)
                            time.sleep(wait)
                        else:
                            raise
                data = _extract_json_object(single_resp.text)
                results_map[a.id] = {
                    "ai_score": max(0, min(100, int(data.get("ai_score", 50)))),
                    "strengths": list(data.get("strengths", []))[:5],
                    "gaps": list(data.get("gaps", []))[:4],
                    "recommendation": data.get("recommendation", "maybe")
                        if data.get("recommendation") in ("strong_fit", "fit", "maybe", "not_fit")
                        else "maybe",
                    "reasoning": str(data.get("reasoning", ""))[:800],
                    "bias_flag": bool(data.get("bias_flag", False)),
                    "bias_notes": str(data.get("bias_notes", ""))[:300],
                }
                ws = weighted_scores.get(a.id, 50)
                rec = results_map[a.id]["recommendation"]
                col = GREEN if rec == "strong_fit" else (CYAN if rec == "fit" else (YELLOW if rec == "maybe" else RED))
                _log(f"  ✓ {a.full_name:<30} {results_map[a.id]['ai_score']:>3}  {col}{rec}{RESET}", "")
            except Exception as inner_exc:
                _log(f"  ✗ {a.full_name} failed: {inner_exc} — using heuristic", YELLOW)
                ws = weighted_scores.get(a.id, 50)
                results_map[a.id] = _heuristic_fallback_single(job, a, ws)

        _log(f"{'━'*60}\n", CYAN)
        return results_map


def analyze_candidate(job, applicant, weighted_score):
    """Single-candidate wrapper (used for compatibility)."""
    results = analyze_batch(job, [applicant], {applicant.id: weighted_score})
    return results[applicant.id]


# ──────────────────────────────────────────────────────────────────────────────
# JD AUTO-EXTRACTION
# ──────────────────────────────────────────────────────────────────────────────

def extract_jd_requirements(jd_text):
    """
    Parse a raw job description text and extract structured requirements.
    Returns dict with title, skills, min_years_experience, education, seniority, description.
    """
    model = _get_model()
    if not model:
        return {"error": "Gemini not available"}

    prompt = f"""You are an expert HR analyst. Extract structured requirements from this job description.
Return ONLY valid JSON, no markdown.

JOB DESCRIPTION:
{jd_text[:4000]}

Return JSON:
{{
  "title": "<inferred job title>",
  "seniority": "<Junior | Mid-Level | Senior | Lead | Principal>",
  "department": "<department if mentioned, else empty>",
  "location": "<location if mentioned, else empty>",
  "employment_type": "<Full-time | Part-time | Contract | Remote>",
  "required_skills": "<comma-separated list of required technical skills>",
  "min_years_experience": <integer, 0 if not specified>,
  "required_education": "<bachelors | masters | phd | diploma | any>",
  "description": "<clean 2-3 paragraph summary of the role>"
}}"""

    try:
        _log("Extracting JD requirements with Gemini...", CYAN)
        resp = model.generate_content(prompt)
        data = _extract_json_object(resp.text)
        _log("JD extraction successful", GREEN)
        return data
    except Exception as exc:
        _log(f"JD extraction failed: {exc}", RED)
        return {"error": str(exc)}
