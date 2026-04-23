import os
import json
import uuid
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    current_app, abort, jsonify,
)
from werkzeug.utils import secure_filename

from extensions import db
from models import Job, Applicant
from services.file_parser import extract_pdf_text
from services.resume_parser import parse_resume_fields

bp = Blueprint("public", __name__)


ALLOWED_RESUME_EXT = {".pdf"}


@bp.route("/")
def landing():
    featured = (
        Job.query.filter_by(is_published=True)
        .order_by(Job.created_at.desc())
        .limit(6)
        .all()
    )
    total_jobs = Job.query.filter_by(is_published=True).count()
    total_applicants = Applicant.query.count()
    return render_template(
        "public/landing.html",
        featured=featured,
        total_jobs=total_jobs,
        total_applicants=total_applicants,
    )


@bp.route("/jobs")
def jobs_list():
    q = (request.args.get("q") or "").strip()
    loc = (request.args.get("location") or "").strip()
    query = Job.query.filter_by(is_published=True)
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Job.title.ilike(like),
                Job.description.ilike(like),
                Job.required_skills.ilike(like),
            )
        )
    if loc:
        query = query.filter(Job.location.ilike(f"%{loc}%"))
    jobs = query.order_by(Job.created_at.desc()).all()
    return render_template("public/jobs_list.html", jobs=jobs, q=q, loc=loc)


@bp.route("/jobs/<int:job_id>")
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    if not job.is_published:
        abort(404)
    related = (
        Job.query.filter(Job.id != job.id, Job.is_published == True)
        .order_by(Job.created_at.desc())
        .limit(3)
        .all()
    )
    return render_template("public/job_detail.html", job=job, related=related)


@bp.route("/jobs/<int:job_id>/apply", methods=["GET", "POST"])
def apply(job_id):
    job = Job.query.get_or_404(job_id)
    if not job.is_published:
        abort(404)

    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        email = (request.form.get("email") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        location = (request.form.get("location") or "").strip()
        skills = (request.form.get("skills") or "").strip()
        years_experience = request.form.get("years_experience") or "0"
        education = (request.form.get("education") or "").strip()
        education_level = (request.form.get("education_level") or "").strip().lower()
        projects = (request.form.get("projects") or "").strip()

        if not full_name or not email:
            flash("Name and email are required.", "error")
            return redirect(url_for("public.apply", job_id=job.id))

        try:
            years_experience = float(years_experience)
        except ValueError:
            years_experience = 0.0

        project_count = 0
        if projects:
            # rough count: split on newlines or semicolons or commas-with-words
            chunks = [c for c in projects.replace(";", "\n").split("\n") if c.strip()]
            project_count = max(1, len(chunks))

        resume_text = ""
        resume_filename = None
        file = request.files.get("resume")
        if file and file.filename:
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in ALLOWED_RESUME_EXT:
                flash("Resume must be a PDF.", "error")
                return redirect(url_for("public.apply", job_id=job.id))
            safe_name = secure_filename(file.filename)
            stored_name = f"{uuid.uuid4().hex}_{safe_name}"
            dest = os.path.join(current_app.config["UPLOAD_FOLDER"], stored_name)
            file.save(dest)
            resume_filename = stored_name
            resume_text = extract_pdf_text(dest)

        # Custom field answers
        custom_answers = {}
        for field in job.custom_fields:
            ans = (request.form.get(f"custom_{field.id}") or "").strip()
            if ans:
                custom_answers[str(field.id)] = ans

        applicant = Applicant(
            job_id=job.id,
            full_name=full_name,
            email=email,
            phone=phone,
            location=location,
            skills=skills,
            years_experience=years_experience,
            education=education,
            education_level=education_level or None,
            projects=projects,
            project_count=project_count,
            resume_filename=resume_filename,
            resume_text=resume_text,
            custom_answers=json.dumps(custom_answers) if custom_answers else None,
            source="web",
            status="new",
        )
        db.session.add(applicant)
        db.session.commit()
        return redirect(url_for("public.apply_success", job_id=job.id, applicant_id=applicant.id))

    return render_template("public/apply.html", job=job)


@bp.route("/jobs/<int:job_id>/parse-resume", methods=["POST"])
def parse_resume(job_id):
    """Accept a PDF upload and return extracted fields as JSON for form autofill."""
    file = request.files.get("resume")
    if not file or not file.filename:
        return jsonify({"ok": False, "error": "No file provided"}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext != ".pdf":
        return jsonify({"ok": False, "error": "Only PDF files are supported"}), 400

    stored_name = f"parse_{uuid.uuid4().hex}.pdf"
    dest = os.path.join(current_app.config["UPLOAD_FOLDER"], stored_name)
    file.save(dest)

    try:
        text = extract_pdf_text(dest)
        fields = parse_resume_fields(text) if text else {}
    finally:
        try:
            os.remove(dest)
        except OSError:
            pass

    return jsonify({"ok": True, "fields": fields, "chars_extracted": len(text) if text else 0})


@bp.route("/jobs/<int:job_id>/apply/success/<int:applicant_id>")
def apply_success(job_id, applicant_id):
    job = Job.query.get_or_404(job_id)
    applicant = Applicant.query.get_or_404(applicant_id)
    if applicant.job_id != job.id:
        abort(404)
    return render_template("public/apply_success.html", job=job, applicant=applicant)
