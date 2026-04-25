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
from services.email_service import (
    send_application_received_email,
    send_new_application_notification,
)

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

        # Umurava Talent Profile Schema fields
        headline = (request.form.get("headline") or "").strip()
        bio = (request.form.get("bio") or "").strip()
        availability_status = (request.form.get("availability_status") or "").strip()
        availability_type = (request.form.get("availability_type") or "").strip()
        linkedin = (request.form.get("linkedin") or "").strip()
        github = (request.form.get("github") or "").strip()
        portfolio_url = (request.form.get("portfolio_url") or "").strip()

        def _parse_json_field(key):
            raw = (request.form.get(key) or "").strip()
            if not raw:
                return None
            try:
                parsed = json.loads(raw)
                return raw if parsed else None
            except Exception:
                return None

        structured_skills = _parse_json_field("structured_skills")
        languages_data = _parse_json_field("languages_data")
        structured_experience = _parse_json_field("structured_experience")
        structured_education = _parse_json_field("structured_education")
        certifications_data = _parse_json_field("certifications_data")
        structured_projects = _parse_json_field("structured_projects")

        # Derive flat skills from structured if the text field was left empty
        if structured_skills and not skills:
            try:
                skill_names = [s.get("name", "").strip() for s in json.loads(structured_skills) if s.get("name")]
                skills = ", ".join(skill_names)
            except Exception:
                pass

        if not full_name or not email:
            flash("Name and email are required.", "error")
            return redirect(url_for("public.apply", job_id=job.id))

        existing = Applicant.query.filter_by(job_id=job.id, email=email).first()
        if existing:
            flash("You've already applied for this role.", "info")
            return redirect(url_for("public.apply_success", job_id=job.id, applicant_id=existing.id))

        try:
            years_experience = float(years_experience)
        except ValueError:
            years_experience = 0.0

        project_count = 0
        if projects:
            chunks = [c for c in projects.replace(";", "\n").split("\n") if c.strip()]
            project_count = max(1, len(chunks))
        elif structured_projects:
            try:
                project_count = len(json.loads(structured_projects))
            except Exception:
                pass

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
            headline=headline or None,
            bio=bio or None,
            structured_skills=structured_skills,
            languages_data=languages_data,
            structured_experience=structured_experience,
            structured_education=structured_education,
            certifications_data=certifications_data,
            structured_projects=structured_projects,
            availability_status=availability_status or None,
            availability_type=availability_type or None,
            linkedin=linkedin or None,
            github=github or None,
            portfolio_url=portfolio_url or None,
        )
        db.session.add(applicant)
        db.session.commit()
        brand = current_app.config.get("BRAND_NAME", "Mpact")
        send_application_received_email(applicant, job, brand)
        if job.recruiter_id:
            dashboard_url = url_for(
                "admin_screening.results", job_id=job.id, _external=True
            )
            send_new_application_notification(applicant, job, brand, dashboard_url)
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


@bp.route("/application/status", methods=["GET", "POST"])
def application_status():
    """Candidate self-service: look up application status by email + reference."""
    applicant = None
    error = None

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        ref = (request.form.get("reference") or "").strip().upper()

        if not email or not ref:
            error = "Please enter both your email address and reference number."
        else:
            # Reference format: MPT-JJJJ-AAAAA
            try:
                parts = ref.split("-")
                if len(parts) == 3 and parts[0] == "MPT":
                    job_id_ref = int(parts[1])
                    applicant_id_ref = int(parts[2])
                    candidate = Applicant.query.filter_by(
                        id=applicant_id_ref, job_id=job_id_ref
                    ).first()
                    if candidate and candidate.email.lower() == email:
                        applicant = candidate
                    else:
                        error = "No application found matching that email and reference number."
                else:
                    error = "Invalid reference number format. It should look like MPT-0001-00001."
            except (ValueError, IndexError):
                error = "Invalid reference number format. It should look like MPT-0001-00001."

    return render_template(
        "public/application_status.html",
        applicant=applicant,
        error=error,
    )
