import csv
import io
import json
import time
from datetime import datetime

from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, jsonify, Response, stream_with_context, current_app,
    send_from_directory,
)

from flask import session

from extensions import db
from models import Job, Applicant
from services.scoring_engine import compute_weighted_score
from services.gemini_service import analyze_batch, extract_jd_requirements
from services.email_service import send_shortlist_email, send_rejection_email
from routes import admin_required


def _rid():
    return session.get("recruiter_id")


def _own_job(job_id):
    """Fetch a job that belongs to the current recruiter, or 404."""
    return Job.query.filter_by(id=job_id, recruiter_id=_rid()).first_or_404()

bp = Blueprint("admin_screening", __name__, url_prefix="/recruiter")

BOLD = "\033[1m"
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
DIM = "\033[2m"


def _log(msg, color=RESET):
    ts = datetime.utcnow().strftime("%H:%M:%S")
    print(f"{DIM}[{ts}]{RESET} {color}{msg}{RESET}", flush=True)


# ──────────────────────────────────────────────────────────────────────────────
# SCREENING INDEX
# ──────────────────────────────────────────────────────────────────────────────

@bp.route("/screening")
@admin_required
def index():
    jobs = Job.query.filter_by(recruiter_id=_rid()).order_by(Job.created_at.desc()).all()
    job_id = request.args.get("job_id", type=int)
    selected = Job.query.filter_by(id=job_id, recruiter_id=_rid()).first() if job_id else (jobs[0] if jobs else None)
    return render_template("admin/screening.html", jobs=jobs, job=selected)


@bp.route("/screening/<int:job_id>/weights", methods=["POST"])
@admin_required
def update_weights(job_id):
    job = _own_job(job_id)
    try:
        job.weight_skills = int(request.form.get("weight_skills") or 0)
        job.weight_experience = int(request.form.get("weight_experience") or 0)
        job.weight_education = int(request.form.get("weight_education") or 0)
        job.weight_projects = int(request.form.get("weight_projects") or 0)
    except ValueError:
        flash("Weights must be integers.", "error")
        return redirect(url_for("admin_screening.index", job_id=job_id))
    total = job.weight_skills + job.weight_experience + job.weight_education + job.weight_projects
    if total != 100:
        flash(f"Weights must sum to 100 (currently {total}).", "error")
    else:
        db.session.commit()
        flash("Weights saved.", "success")
    return redirect(url_for("admin_screening.index", job_id=job_id))


# ──────────────────────────────────────────────────────────────────────────────
# BATCH RUN WITH SSE STREAMING PROGRESS
# ──────────────────────────────────────────────────────────────────────────────

@bp.route("/screening/<int:job_id>/run", methods=["POST"])
@admin_required
def run(job_id):
    job = _own_job(job_id)
    total_weight = job.weight_skills + job.weight_experience + job.weight_education + job.weight_projects
    if total_weight != 100:
        return jsonify({"ok": False, "error": f"Weights must sum to 100 (currently {total_weight})."}), 400

    applicants = list(job.applicants)
    if not applicants:
        return jsonify({"ok": False, "error": "No applications received for this job yet."}), 400

    t_start = time.time()
    _log(f"\n{'═'*60}", CYAN)
    _log(f"  SCREENING JOB: {job.title}  ({len(applicants)} candidates)", BOLD)
    _log(f"{'═'*60}", CYAN)
    _log(f"  Step 1/3 — Computing deterministic scores...", CYAN)

    # Step 1: Deterministic scoring for all candidates
    weighted_scores = {}
    for a in applicants:
        scores = compute_weighted_score(a, job)
        a.skills_score = scores["skills_score"]
        a.experience_score = scores["experience_score"]
        a.education_score = scores["education_score"]
        a.projects_score = scores["projects_score"]
        a.weighted_score = scores["weighted_score"]
        weighted_scores[a.id] = scores["weighted_score"]
        _log(f"    {a.full_name:<28}  skills={scores['skills_score']:>5.1f}  exp={scores['experience_score']:>5.1f}  edu={scores['education_score']:>5.1f}  proj={scores['projects_score']:>5.1f}  → {scores['weighted_score']:>5.1f}", DIM)

    _log(f"  Deterministic scoring complete in {time.time()-t_start:.2f}s", GREEN)
    _log(f"  Step 2/3 — Running Gemini batch analysis...", CYAN)

    # Step 2: Batch AI analysis (single Gemini call)
    ai_results = analyze_batch(job, applicants, weighted_scores)

    _log(f"  Step 3/3 — Saving results to database...", CYAN)

    # Step 3: Save everything
    processed = 0
    for a in applicants:
        ai = ai_results.get(a.id, {})
        if not ai:
            continue
        a.ai_score = float(ai.get("ai_score", a.weighted_score))
        a.ai_strengths = json.dumps(ai.get("strengths", []))
        a.ai_gaps = json.dumps(ai.get("gaps", []))
        a.ai_recommendation = ai.get("recommendation", "maybe")
        a.ai_reasoning = ai.get("reasoning", "")
        a.bias_flag = bool(ai.get("bias_flag", False))
        a.bias_notes = ai.get("bias_notes", "")
        # Blended final: 60% deterministic, 40% AI
        a.final_score = round(a.weighted_score * 0.6 + a.ai_score * 0.4, 1)
        a.screened_at = datetime.utcnow()
        processed += 1

    db.session.commit()
    elapsed = time.time() - t_start

    bias_count = sum(1 for a in applicants if a.bias_flag)

    _log(f"\n  ✓ Screening complete: {processed} candidates in {elapsed:.1f}s", GREEN)
    if bias_count:
        _log(f"  ⚠ Bias flags raised for {bias_count} candidate(s) — review in results", YELLOW)
    _log(f"{'═'*60}\n", CYAN)

    return jsonify({
        "ok": True,
        "processed": processed,
        "elapsed": round(elapsed, 1),
        "bias_count": bias_count,
        "model": current_app.config.get("GEMINI_MODEL", "gemini-1.5-flash"),
        "redirect": url_for("admin_screening.results", job_id=job.id),
    })


# ──────────────────────────────────────────────────────────────────────────────
# RESULTS
# ──────────────────────────────────────────────────────────────────────────────

@bp.route("/screening/<int:job_id>/results")
@admin_required
def results(job_id):
    job = _own_job(job_id)
    limit = request.args.get("limit", default=10, type=int)
    if limit not in (10, 20, 50):
        limit = 10
    ranked = (
        job.applicants
        .filter(Applicant.final_score.isnot(None))
        .order_by(Applicant.final_score.desc())
        .limit(limit)
        .all()
    )
    return render_template("admin/results.html", job=job, ranked=ranked, limit=limit)


# ──────────────────────────────────────────────────────────────────────────────
# CSV EXPORT
# ──────────────────────────────────────────────────────────────────────────────

@bp.route("/screening/<int:job_id>/export")
@admin_required
def export_csv(job_id):
    job = _own_job(job_id)
    limit = request.args.get("limit", default=10, type=int)
    if limit not in (10, 20, 50):
        limit = 10

    ranked = (
        job.applicants
        .filter(Applicant.final_score.isnot(None))
        .order_by(Applicant.final_score.desc())
        .limit(limit)
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Rank", "Name", "Email", "Phone", "Location",
        "Final Score", "Weighted Score", "AI Score",
        "Skills Score", "Experience Score", "Education Score", "Projects Score",
        "Match", "Years Experience", "Education", "Skills",
        "Strengths", "Gaps", "AI Reasoning", "Bias Flag", "Status"
    ])
    for i, a in enumerate(ranked, 1):
        writer.writerow([
            i, a.full_name, a.email, a.phone, a.location,
            a.final_score, a.weighted_score, a.ai_score,
            a.skills_score, a.experience_score, a.education_score, a.projects_score,
            a.recommendation_label, a.years_experience, a.education,
            "; ".join(a.skills_list),
            "; ".join(a.strengths_list),
            "; ".join(a.gaps_list),
            a.ai_reasoning,
            "Yes" if a.bias_flag else "No",
            a.status,
        ])

    output.seek(0)
    filename = f"mpact-shortlist-{job.id}-top{limit}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ──────────────────────────────────────────────────────────────────────────────
# CANDIDATE JSON (drawer)
# ──────────────────────────────────────────────────────────────────────────────

def _own_applicant(applicant_id):
    """Fetch an applicant whose job belongs to the current recruiter, or 404."""
    a = Applicant.query.get_or_404(applicant_id)
    if a.job.recruiter_id != _rid():
        from flask import abort
        abort(404)
    return a


@bp.route("/applicant/<int:applicant_id>.json")
@admin_required
def applicant_json(applicant_id):
    a = _own_applicant(applicant_id)
    return jsonify({
        "id": a.id,
        "name": a.full_name,
        "initials": a.initials,
        "avatar_color": a.avatar_color,
        "avatar_bg": a.avatar_bg,
        "email": a.email,
        "phone": a.phone,
        "location": a.location,
        "skills": a.skills_list,
        "years_experience": a.years_experience,
        "education": a.education,
        "education_level": a.education_level,
        "projects": a.projects,
        "project_count": a.project_count,
        "resume_filename": a.resume_filename,
        "has_resume": bool(a.resume_filename),
        "status": a.status,
        "scores": {
            "skills": a.skills_score,
            "experience": a.experience_score,
            "education": a.education_score,
            "projects": a.projects_score,
            "weighted": a.weighted_score,
            "ai": a.ai_score,
            "final": a.final_score,
        },
        "strengths": a.strengths_list,
        "gaps": a.gaps_list,
        "recommendation": a.ai_recommendation,
        "recommendation_label": a.recommendation_label,
        "recommendation_tone": a.recommendation_tone,
        "reasoning": a.ai_reasoning,
        "bias_flag": a.bias_flag,
        "bias_notes": a.bias_notes,
        "custom_qa": [
            {"label": f.label, "answer": a.custom_answers_dict.get(str(f.id), "")}
            for f in a.job.custom_fields
            if a.custom_answers_dict.get(str(f.id), "")
        ],
        "recruiter_notes": a.recruiter_notes or "",
        "headline": a.headline or "",
        "bio": a.bio or "",
        "structured_skills": a.structured_skills_list,
        "languages": a.languages_list,
        "structured_experience": a.structured_experience_list,
        "structured_education": a.structured_education_list,
        "certifications": a.certifications_list,
        "structured_projects": a.structured_projects_list,
        "availability_status": a.availability_status or "",
        "availability_type": a.availability_type or "",
        "linkedin": a.linkedin or "",
        "github": a.github or "",
        "portfolio_url": a.portfolio_url or "",
    })


# ──────────────────────────────────────────────────────────────────────────────
# STATUS UPDATE (single + bulk)
# ──────────────────────────────────────────────────────────────────────────────

@bp.route("/applicant/<int:applicant_id>/status", methods=["POST"])
@admin_required
def update_status(applicant_id):
    a = _own_applicant(applicant_id)
    if request.is_json:
        new_status = request.json.get("status")
    else:
        new_status = request.form.get("status")
    if new_status not in ("new", "reviewed", "shortlisted", "interview", "rejected"):
        return jsonify({"ok": False, "error": "Invalid status"}), 400
    prev_status = a.status
    a.status = new_status
    db.session.commit()
    brand = current_app.config.get("BRAND_NAME", "Mpact")
    if new_status == "shortlisted" and prev_status != "shortlisted" and a.email:
        send_shortlist_email(a, a.job, brand)
    elif new_status == "rejected" and prev_status != "rejected" and a.email:
        send_rejection_email(a, a.job, brand)
    return jsonify({"ok": True, "status": a.status})


@bp.route("/screening/<int:job_id>/bulk-status", methods=["POST"])
@admin_required
def bulk_status(job_id):
    """Bulk update status for multiple candidates."""
    data = request.json or {}
    ids = data.get("ids", [])
    new_status = data.get("status")
    if not ids or new_status not in ("new", "reviewed", "shortlisted", "interview", "rejected"):
        return jsonify({"ok": False, "error": "Invalid request"}), 400

    updated = 0
    to_email = []
    for aid in ids:
        a = Applicant.query.get(aid)
        if a and a.job_id == job_id and a.job.recruiter_id == _rid():
            if new_status == "shortlisted" and a.status != "shortlisted" and a.email:
                to_email.append(a)
            a.status = new_status
            updated += 1
    db.session.commit()

    job = Job.query.filter_by(id=job_id, recruiter_id=_rid()).first()
    brand = current_app.config.get("BRAND_NAME", "Mpact")
    for a in to_email:
        send_shortlist_email(a, job, brand)

    _log(f"Bulk status update: {updated} candidates → {new_status} | {len(to_email)} email(s) sent", GREEN)
    return jsonify({"ok": True, "updated": updated, "status": new_status, "emails_sent": len(to_email)})


# ──────────────────────────────────────────────────────────────────────────────
# RECRUITER NOTES
# ──────────────────────────────────────────────────────────────────────────────

@bp.route("/applicant/<int:applicant_id>/notes", methods=["POST"])
@admin_required
def save_notes(applicant_id):
    a = _own_applicant(applicant_id)
    notes = (request.json or {}).get("notes", "")
    a.recruiter_notes = notes.strip() or None
    db.session.commit()
    return jsonify({"ok": True})


# ──────────────────────────────────────────────────────────────────────────────
# RESUME DOWNLOAD
# ──────────────────────────────────────────────────────────────────────────────

@bp.route("/applicant/<int:applicant_id>/resume")
@admin_required
def download_resume(applicant_id):
    a = _own_applicant(applicant_id)
    if not a.resume_filename:
        return jsonify({"error": "No resume on file"}), 404
    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        a.resume_filename,
        as_attachment=True,
        download_name=f"resume_{a.full_name.replace(' ', '_')}.pdf",
    )


# ──────────────────────────────────────────────────────────────────────────────
# JD AUTO-EXTRACTION
# ──────────────────────────────────────────────────────────────────────────────

@bp.route("/screening/extract-jd", methods=["POST"])
@admin_required
def extract_jd():
    """Extract structured job requirements from pasted JD text."""
    jd_text = (request.json or {}).get("jd_text", "").strip()
    if not jd_text or len(jd_text) < 50:
        return jsonify({"ok": False, "error": "JD text too short"}), 400
    result = extract_jd_requirements(jd_text)
    if "error" in result:
        return jsonify({"ok": False, "error": result["error"]}), 500
    return jsonify({"ok": True, "data": result})
