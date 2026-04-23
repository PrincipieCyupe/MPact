import os
from flask import Flask, render_template, session

from config import Config
from extensions import db


def _migrate_db(db):
    """Add new columns to existing DB without losing data."""
    migrations = [
        "ALTER TABLE applicants ADD COLUMN bias_flag BOOLEAN DEFAULT 0",
        "ALTER TABLE applicants ADD COLUMN bias_notes TEXT",
        "ALTER TABLE jobs ADD COLUMN recruiter_id INTEGER REFERENCES recruiters(id)",
        "ALTER TABLE recruiters ADD COLUMN is_verified BOOLEAN DEFAULT 0",
        "ALTER TABLE recruiters ADD COLUMN verification_token VARCHAR(100)",
        "ALTER TABLE recruiters ADD COLUMN token_expires_at DATETIME",
        "ALTER TABLE applicants ADD COLUMN custom_answers TEXT",
    ]
    with db.engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(db.text(sql))
                conn.commit()
            except Exception:
                pass  # Column already exists — safe to ignore


def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(Config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), "instance"), exist_ok=True)

    db.init_app(app)

    # Blueprints
    from routes.public import bp as public_bp
    from routes.admin_auth import bp as admin_auth_bp
    from routes.admin_jobs import bp as admin_jobs_bp
    from routes.admin_screening import bp as admin_screening_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_auth_bp)
    app.register_blueprint(admin_jobs_bp)
    app.register_blueprint(admin_screening_bp)

    @app.context_processor
    def inject_globals():
        from models import Recruiter
        recruiter = None
        rid = session.get("recruiter_id")
        if rid:
            recruiter = Recruiter.query.get(rid)
        return {
            "brand_name":    app.config.get("BRAND_NAME", "Mpact"),
            "brand_tagline": app.config.get("BRAND_TAGLINE", ""),
            "team_name":     app.config.get("TEAM_NAME", ""),
            "current_recruiter": recruiter,
        }

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(e):
        return render_template("errors/404.html", message="File too large (max 16 MB)."), 413

    with app.app_context():
        import models  # noqa: F401
        db.create_all()
        _migrate_db(db)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
