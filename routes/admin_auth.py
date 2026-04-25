import secrets
from datetime import datetime, timedelta

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session, current_app,
)

from extensions import db
from models import Recruiter
from services.email import send_verification_email

bp = Blueprint("admin_auth", __name__, url_prefix="/recruiter")


def _make_token() -> str:
    return secrets.token_urlsafe(32)


def _set_token(recruiter: Recruiter) -> str:
    token = _make_token()
    recruiter.verification_token = token
    recruiter.token_expires_at   = datetime.utcnow() + timedelta(hours=24)
    return token


@bp.route("/register", methods=["GET", "POST"])
def register():
    if session.get("recruiter_id") and session.get("recruiter_verified"):
        return redirect(url_for("admin_jobs.dashboard"))

    if request.method == "POST":
        name    = (request.form.get("name") or "").strip()
        email   = (request.form.get("email") or "").strip().lower()
        company = (request.form.get("company") or "").strip()
        password = request.form.get("password") or ""
        confirm  = request.form.get("confirm") or ""

        error = None
        if not name:
            error = "Full name is required."
        elif not email or "@" not in email:
            error = "A valid email address is required."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        elif password != confirm:
            error = "Passwords do not match."
        elif Recruiter.query.filter_by(email=email).first():
            error = "An account with that email already exists."

        if error:
            flash(error, "error")
            return render_template("admin/register.html",
                                   name=name, email=email, company=company)

        recruiter = Recruiter(name=name, email=email, company=company or None)
        recruiter.set_password(password)
        token = _set_token(recruiter)
        db.session.add(recruiter)
        db.session.commit()

        verify_url = url_for("admin_auth.verify_email", token=token, _external=True)
        mail_configured = bool(
            current_app.config.get("MAIL_SERVER") or current_app.config.get("RESEND_API_KEY")
        )
        sent = send_verification_email(email, name, verify_url)

        session["_pending_verify_email"] = email
        session["_pending_verify_name"]  = name
        if not sent:
            session["_dev_verify_url"] = verify_url
            if mail_configured:
                session["_email_error"] = True

        return redirect(url_for("admin_auth.verify_pending"))

    return render_template("admin/register.html", name="", email="", company="")


@bp.route("/verify-pending")
def verify_pending():
    email       = session.get("_pending_verify_email", "")
    name        = session.get("_pending_verify_name", "")
    dev_url     = session.pop("_dev_verify_url", None)
    email_error = session.pop("_email_error", False)
    return render_template("admin/verify_pending.html",
                           email=email, name=name,
                           dev_url=dev_url, email_error=email_error)


@bp.route("/verify/<token>")
def verify_email(token):
    recruiter = Recruiter.query.filter_by(verification_token=token).first()

    if not recruiter:
        flash("This verification link is invalid or has already been used.", "error")
        return redirect(url_for("admin_auth.login"))

    if recruiter.token_expires_at and datetime.utcnow() > recruiter.token_expires_at:
        flash("This verification link has expired. Please request a new one.", "error")
        session["_pending_verify_email"] = recruiter.email
        session["_pending_verify_name"]  = recruiter.name
        return redirect(url_for("admin_auth.verify_pending"))

    recruiter.is_verified        = True
    recruiter.verification_token = None
    recruiter.token_expires_at   = None
    db.session.commit()

    session.pop("_pending_verify_email", None)
    session.pop("_pending_verify_name", None)

    session["recruiter_id"]       = recruiter.id
    session["recruiter_name"]     = recruiter.name
    session["recruiter_verified"] = True

    flash(f"Email verified! Welcome to {current_app.config.get('BRAND_NAME', 'Mpact')}, {recruiter.first_name}.", "success")
    return redirect(url_for("admin_jobs.dashboard"))


@bp.route("/resend-verification", methods=["POST"])
def resend_verification():
    email = (request.form.get("email") or session.get("_pending_verify_email") or "").strip().lower()
    recruiter = Recruiter.query.filter_by(email=email).first() if email else None

    if not recruiter:
        flash("We couldn't find an account with that email.", "error")
        return redirect(url_for("admin_auth.verify_pending"))

    if recruiter.is_verified:
        flash("This account is already verified. Please sign in.", "info")
        return redirect(url_for("admin_auth.login"))

    token = _set_token(recruiter)
    db.session.commit()

    verify_url = url_for("admin_auth.verify_email", token=token, _external=True)
    mail_configured = bool(
        current_app.config.get("MAIL_SERVER") or current_app.config.get("RESEND_API_KEY")
    )
    sent = send_verification_email(recruiter.email, recruiter.name, verify_url)

    session["_pending_verify_email"] = recruiter.email
    session["_pending_verify_name"]  = recruiter.name
    if not sent:
        session["_dev_verify_url"] = verify_url
        if mail_configured:
            session["_email_error"] = True
            flash("Email sending failed — check Deploy Logs on Railway for the error.", "error")
        else:
            flash("No email transport configured — use the link below.", "info")
    else:
        flash("Verification email resent — check your inbox.", "success")

    return redirect(url_for("admin_auth.verify_pending"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("recruiter_id") and session.get("recruiter_verified"):
        return redirect(url_for("admin_jobs.dashboard"))

    if request.method == "POST":
        email    = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        recruiter = Recruiter.query.filter_by(email=email).first()

        if recruiter and recruiter.check_password(password):
            if not recruiter.is_verified:
                session["_pending_verify_email"] = recruiter.email
                session["_pending_verify_name"]  = recruiter.name
                flash("Please verify your email before signing in.", "info")
                return redirect(url_for("admin_auth.verify_pending"))

            session["recruiter_id"]       = recruiter.id
            session["recruiter_name"]     = recruiter.name
            session["recruiter_verified"] = True
            flash(f"Welcome back, {recruiter.first_name}.", "success")
            nxt = request.args.get("next") or url_for("admin_jobs.dashboard")
            return redirect(nxt)

        flash("Invalid email or password.", "error")
        return render_template("admin/login.html", email=email)

    return render_template("admin/login.html", email="")


@bp.route("/logout", methods=["POST", "GET"])
def logout():
    session.pop("recruiter_id", None)
    session.pop("recruiter_name", None)
    session.pop("recruiter_verified", None)
    session.pop("admin_logged_in", None)
    flash("You've been signed out.", "info")
    return redirect(url_for("public.landing"))
