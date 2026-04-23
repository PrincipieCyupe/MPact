import csv
import io
import json
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, abort
from sqlalchemy import func, desc

from extensions import db
from models import Job, JobField, Applicant
from routes import admin_required

bp = Blueprint("admin_jobs", __name__, url_prefix="/recruiter")


def _rid():
    """Current recruiter's ID from session."""
    return session.get("recruiter_id")


def _own_job(job_id):
    """Fetch a job that belongs to the current recruiter, or 404."""
    job = Job.query.filter_by(id=job_id, recruiter_id=_rid()).first_or_404()
    return job


def _my_jobs_subquery():
    """Subquery of job IDs owned by the current recruiter."""
    return db.session.query(Job.id).filter(Job.recruiter_id == _rid()).subquery()


@bp.route("/")
@admin_required
def dashboard():
    rid = _rid()

    job_count = (
        db.session.query(func.count(Job.id))
        .filter(Job.recruiter_id == rid)
        .scalar() or 0
    )

    my_jobs = _my_jobs_subquery()

    applicant_count = (
        db.session.query(func.count(Applicant.id))
        .filter(Applicant.job_id.in_(my_jobs))
        .scalar() or 0
    )
    screened_count = (
        db.session.query(func.count(Applicant.id))
        .filter(Applicant.job_id.in_(my_jobs), Applicant.final_score.isnot(None))
        .scalar() or 0
    )
    avg_score = (
        db.session.query(func.avg(Applicant.final_score))
        .filter(Applicant.job_id.in_(my_jobs), Applicant.final_score.isnot(None))
        .scalar()
    )
    shortlist_count = (
        db.session.query(func.count(Applicant.id))
        .filter(
            Applicant.job_id.in_(my_jobs),
            Applicant.ai_recommendation.in_(["strong_fit", "fit"]),
        )
        .scalar() or 0
    )

    recent_jobs = (
        Job.query
        .filter(Job.recruiter_id == rid)
        .order_by(desc(Job.created_at))
        .limit(6).all()
    )
    top_candidates = (
        Applicant.query
        .filter(Applicant.job_id.in_(my_jobs), Applicant.final_score.isnot(None))
        .order_by(desc(Applicant.final_score))
        .limit(6).all()
    )

    return render_template(
        "admin/dashboard.html",
        job_count=job_count,
        applicant_count=applicant_count,
        screened_count=screened_count,
        shortlist_count=shortlist_count,
        avg_score=round(avg_score, 1) if avg_score else None,
        recent_jobs=recent_jobs,
        top_candidates=top_candidates,
        now_hour=datetime.now().hour,
    )


@bp.route("/jobs")
@admin_required
def jobs_list():
    jobs = (
        Job.query
        .filter(Job.recruiter_id == _rid())
        .order_by(desc(Job.created_at))
        .all()
    )
    return render_template("admin/jobs_list.html", jobs=jobs)


@bp.route("/jobs/new", methods=["GET", "POST"])
@admin_required
def job_create():
    if request.method == "POST":
        job = _job_from_form(Job())
        job.recruiter_id = _rid()
        if not job.title:
            flash("Job title is required.", "error")
            return redirect(url_for("admin_jobs.job_create"))
        db.session.add(job)
        db.session.flush()
        _save_custom_fields(job)
        db.session.commit()
        flash("Job posted.", "success")
        return redirect(url_for("admin_jobs.job_detail", job_id=job.id))
    return render_template("admin/job_form.html", job=None, custom_fields_json="[]")


@bp.route("/jobs/<int:job_id>")
@admin_required
def job_detail(job_id):
    job = _own_job(job_id)
    applicants = (
        job.applicants
        .order_by(Applicant.final_score.desc().nullslast(), Applicant.created_at.desc())
        .all()
    )
    return render_template("admin/job_detail.html", job=job, applicants=applicants)


@bp.route("/jobs/<int:job_id>/edit", methods=["GET", "POST"])
@admin_required
def job_edit(job_id):
    job = _own_job(job_id)
    if request.method == "POST":
        _job_from_form(job)
        _save_custom_fields(job)
        db.session.commit()
        flash("Job updated.", "success")
        return redirect(url_for("admin_jobs.job_detail", job_id=job.id))
    fields_json = json.dumps([f.to_dict() for f in job.custom_fields])
    return render_template("admin/job_form.html", job=job, custom_fields_json=fields_json)


@bp.route("/jobs/<int:job_id>/delete", methods=["POST"])
@admin_required
def job_delete(job_id):
    job = _own_job(job_id)
    db.session.delete(job)
    db.session.commit()
    flash("Job deleted.", "success")
    return redirect(url_for("admin_jobs.jobs_list"))


@bp.route("/jobs/<int:job_id>/import", methods=["GET", "POST"])
@admin_required
def import_csv(job_id):
    job = _own_job(job_id)
    if request.method == "POST":
        file = request.files.get("csv_file")
        if not file or not file.filename:
            flash("Please select a CSV file.", "error")
            return redirect(url_for("admin_jobs.import_csv", job_id=job_id))

        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext not in ("csv", "tsv"):
            flash("Only CSV/TSV files are supported.", "error")
            return redirect(url_for("admin_jobs.import_csv", job_id=job_id))

        content = file.read().decode("utf-8-sig", errors="replace")
        reader = csv.DictReader(io.StringIO(content))
        imported = 0
        skipped = 0
        errors = []

        COLUMN_MAP = {
            "full_name": ["full_name", "name", "fullname", "candidate name", "applicant name"],
            "email": ["email", "email address", "e-mail"],
            "phone": ["phone", "phone number", "mobile", "tel"],
            "location": ["location", "city", "country", "address"],
            "skills": ["skills", "technical skills", "skill set", "technologies"],
            "years_experience": ["years_experience", "years experience", "experience", "exp", "years"],
            "education": ["education", "degree", "qualification", "school"],
            "education_level": ["education_level", "education level", "degree level"],
            "projects": ["projects", "portfolio", "project description", "work samples"],
        }

        def find_col(row, aliases):
            lower_keys = {k.lower(): k for k in row.keys()}
            for alias in aliases:
                if alias in lower_keys:
                    return row.get(lower_keys[alias], "").strip()
            return ""

        for row_num, row in enumerate(reader, 2):
            try:
                full_name = find_col(row, COLUMN_MAP["full_name"])
                email = find_col(row, COLUMN_MAP["email"])
                if not full_name:
                    skipped += 1
                    continue

                years_exp_raw = find_col(row, COLUMN_MAP["years_experience"])
                try:
                    years_experience = float(years_exp_raw) if years_exp_raw else 0.0
                except ValueError:
                    years_experience = 0.0

                projects_text = find_col(row, COLUMN_MAP["projects"])
                project_count = 0
                if projects_text:
                    chunks = [c for c in projects_text.replace(";", "\n").split("\n") if c.strip()]
                    project_count = max(1, len(chunks))

                edu_level = find_col(row, COLUMN_MAP["education_level"]).lower()
                if edu_level not in ("phd", "masters", "bachelors", "diploma", "highschool", "none"):
                    edu_level = None

                applicant = Applicant(
                    job_id=job.id,
                    full_name=full_name,
                    email=email or None,
                    phone=find_col(row, COLUMN_MAP["phone"]) or None,
                    location=find_col(row, COLUMN_MAP["location"]) or None,
                    skills=find_col(row, COLUMN_MAP["skills"]) or None,
                    years_experience=years_experience,
                    education=find_col(row, COLUMN_MAP["education"]) or None,
                    education_level=edu_level,
                    projects=projects_text or None,
                    project_count=project_count,
                    source="csv",
                    status="new",
                )
                db.session.add(applicant)
                imported += 1
            except Exception as exc:
                errors.append(f"Row {row_num}: {exc}")

        db.session.commit()

        if imported:
            flash(f"Imported {imported} candidate(s)." + (f" Skipped {skipped}." if skipped else ""), "success")
        else:
            flash("No candidates imported. Check your CSV format.", "error")
        if errors:
            flash(f"Errors on {len(errors)} row(s): {'; '.join(errors[:3])}", "error")

        return redirect(url_for("admin_jobs.job_detail", job_id=job_id))

    return render_template("admin/import_csv.html", job=job)


def _save_custom_fields(job):
    raw = (request.form.get("custom_fields_json") or "[]").strip()
    try:
        fields_data = json.loads(raw)
        if not isinstance(fields_data, list):
            fields_data = []
    except (ValueError, TypeError):
        fields_data = []

    JobField.query.filter_by(job_id=job.id).delete()
    for idx, fd in enumerate(fields_data):
        label = (fd.get("label") or "").strip()
        if not label:
            continue
        ftype = fd.get("type", "text")
        if ftype not in ("text", "textarea", "yesno", "select"):
            ftype = "text"
        opts = fd.get("options", [])
        opts_json = json.dumps([o for o in opts if o]) if isinstance(opts, list) else "[]"
        field = JobField(
            job_id=job.id,
            label=label,
            field_type=ftype,
            options=opts_json if opts_json != "[]" else None,
            required=bool(fd.get("required", False)),
            sort_order=idx,
        )
        db.session.add(field)


def _job_from_form(job):
    job.title = (request.form.get("title") or "").strip()
    job.department = (request.form.get("department") or "").strip()
    job.location = (request.form.get("location") or "").strip()
    job.employment_type = (request.form.get("employment_type") or "").strip()
    job.seniority = (request.form.get("seniority") or "").strip()
    job.description = (request.form.get("description") or "").strip()
    job.required_skills = (request.form.get("required_skills") or "").strip()
    try:
        job.min_years_experience = int(request.form.get("min_years_experience") or 0)
    except ValueError:
        job.min_years_experience = 0
    job.required_education = (request.form.get("required_education") or "").strip()
    job.is_published = bool(request.form.get("is_published"))
    return job
