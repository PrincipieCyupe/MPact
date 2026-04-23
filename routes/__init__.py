from functools import wraps
from flask import session, redirect, url_for, request, flash


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("recruiter_id"):
            flash("Please sign in to access the recruiter dashboard.", "info")
            return redirect(url_for("admin_auth.login", next=request.path))
        if not session.get("recruiter_verified"):
            flash("Please verify your email address to access the dashboard.", "info")
            return redirect(url_for("admin_auth.verify_pending"))
        return fn(*args, **kwargs)
    return wrapper


# Alias so existing code using either name works
recruiter_required = admin_required
