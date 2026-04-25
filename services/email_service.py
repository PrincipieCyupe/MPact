"""
Email notifications for recruiting events.
Transport priority: Resend API (RESEND_API_KEY) → SMTP (MAIL_SERVER).
Fails silently with a console log when neither is configured.
"""
import json
import smtplib
import ssl
import urllib.error
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import Config


# ─── transport helpers ───────────────────────────────────────────────────────

def _resend_ok():
    return bool(Config.RESEND_API_KEY)


def _smtp_ok():
    return bool(Config.MAIL_SERVER and Config.MAIL_USERNAME and Config.MAIL_PASSWORD)


def _from_addr():
    return Config.MAIL_FROM or Config.MAIL_USERNAME or "no-reply@mpact.rw"


def _send_via_resend(to_email, subject, html, plain, brand_name):
    payload = json.dumps({
        "from": f"{brand_name} <{_from_addr()}>",
        "to":   [to_email],
        "subject": subject,
        "html": html,
        "text": plain,
    }).encode()
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {Config.RESEND_API_KEY}",
            "Content-Type":  "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            print(f"[email/resend] ✓ '{subject}' → {to_email} id={result.get('id','')}", flush=True)
            return True
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        print(f"[email/resend] ✗ HTTP {exc.code}: {body}", flush=True)
        return False
    except Exception as exc:
        print(f"[email/resend] ✗ {exc}", flush=True)
        return False


def _send_via_smtp(to_email, subject, html, plain, brand_name):
    from_addr = _from_addr()
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"{brand_name} <{from_addr}>"
    msg["To"]      = to_email
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html,  "html"))
    try:
        ctx  = ssl.create_default_context()
        port = int(Config.MAIL_PORT or 587)
        if port == 465:
            with smtplib.SMTP_SSL(Config.MAIL_SERVER, port, context=ctx) as server:
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.sendmail(from_addr, to_email, msg.as_string())
        else:
            with smtplib.SMTP(Config.MAIL_SERVER, port) as server:
                server.ehlo()
                server.starttls(context=ctx)
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.sendmail(from_addr, to_email, msg.as_string())
        print(f"[email/smtp] ✓ '{subject}' → {to_email}", flush=True)
        return True
    except Exception as exc:
        print(f"[email/smtp] ✗ {exc}", flush=True)
        return False


def _send(to_email, subject, html, plain, brand_name):
    """Route through Resend (preferred) or SMTP. Silently skip if neither configured."""
    if _resend_ok():
        return _send_via_resend(to_email, subject, html, plain, brand_name)
    if _smtp_ok():
        return _send_via_smtp(to_email, subject, html, plain, brand_name)
    print(f"[email] No transport configured — skipping '{subject}' to {to_email}", flush=True)
    return False


# ─── candidate emails ─────────────────────────────────────────────────────────

def send_application_received_email(applicant, job, brand_name="Mpact"):
    """Confirm to the candidate that their application was received."""
    if not applicant.email:
        return False
    ref   = f"MPT-{job.id:04d}-{applicant.id:05d}"
    first = applicant.full_name.split()[0]
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#F5F5F7;font-family:'Inter',system-ui,sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:48px 20px">
    <table width="520" cellpadding="0" cellspacing="0"
           style="background:#fff;border-radius:16px;overflow:hidden;border:1px solid #E5E7EB">
      <tr><td style="background:#09090B;padding:28px 40px">
        <span style="font-size:18px;font-weight:800;color:#fff;letter-spacing:-.025em">{brand_name}</span>
      </td></tr>
      <tr><td style="padding:40px">
        <p style="margin:0 0 4px;font-size:12px;font-weight:700;color:#635BFF;text-transform:uppercase;letter-spacing:.06em">Application Received</p>
        <h1 style="margin:0 0 16px;font-size:24px;font-weight:800;color:#09090B;letter-spacing:-.03em">We got your application, {first}.</h1>
        <p style="margin:0 0 16px;color:#6B7280;font-size:15px;line-height:1.65">
          Thank you for applying for <strong style="color:#09090B">{job.title}</strong>
          {f"at <strong style='color:#09090B'>{job.department}</strong>" if job.department else ""}.
          Your application is now in our system.
        </p>
        <div style="background:#F9FAFB;border-radius:10px;padding:16px 20px;margin:0 0 24px;border:1px solid #E5E7EB">
          <p style="margin:0 0 6px;font-size:12px;font-weight:700;color:#9CA3AF;text-transform:uppercase;letter-spacing:.05em">Reference number</p>
          <p style="margin:0;font-family:'JetBrains Mono',monospace;font-size:18px;font-weight:700;color:#09090B;letter-spacing:.05em">{ref}</p>
        </div>
        <p style="margin:0 0 6px;font-size:13px;font-weight:700;color:#09090B">What happens next?</p>
        <table cellpadding="0" cellspacing="0" style="width:100%;margin-bottom:24px">
          {"".join(f'<tr><td style="width:28px;vertical-align:top;padding:6px 0"><div style="width:22px;height:22px;background:#635BFF;border-radius:50%;text-align:center;line-height:22px;font-size:11px;font-weight:700;color:#fff">{n}</div></td><td style="padding:6px 0 6px 10px;font-size:13px;color:#6B7280;line-height:1.5">{t}</td></tr>' for n, t in [(1, "AI screens your profile against the role requirements — usually within 24 hours"), (2, "A recruiter reviews the AI results and makes the final shortlist decision"), (3, "You'll receive an email if you're shortlisted for the next stage")])}
        </table>
        <p style="margin:0;font-size:13px;color:#9CA3AF;line-height:1.6">
          Keep this reference number in case you need to follow up.<br>Questions? Reply to this email.
        </p>
      </td></tr>
      <tr><td style="padding:16px 40px;border-top:1px solid #E5E7EB">
        <p style="margin:0;font-size:11px;color:#C4C4C4">{brand_name} · Built with care in Kigali, Rwanda</p>
      </td></tr>
    </table>
  </td></tr></table>
</body></html>"""
    plain = (
        f"Hi {first},\n\nYour application for {job.title} has been received.\n"
        f"Reference: {ref}\n\n"
        f"What's next:\n"
        f"1. AI screens your profile (within 24 hours)\n"
        f"2. Recruiter reviews results and makes final shortlist\n"
        f"3. You'll hear from us if shortlisted\n\n"
        f"Thank you,\n{brand_name} Recruiting Team"
    )
    return _send(applicant.email, f"Application received — {job.title}", html, plain, brand_name)


def send_rejection_email(applicant, job, brand_name="Mpact"):
    """Notify candidate their application was not successful."""
    if not applicant.email:
        return False
    first = applicant.full_name.split()[0]
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#F5F5F7;font-family:'Inter',system-ui,sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:48px 20px">
    <table width="520" cellpadding="0" cellspacing="0"
           style="background:#fff;border-radius:16px;overflow:hidden;border:1px solid #E5E7EB">
      <tr><td style="background:#09090B;padding:28px 40px">
        <span style="font-size:18px;font-weight:800;color:#fff;letter-spacing:-.025em">{brand_name}</span>
      </td></tr>
      <tr><td style="padding:40px">
        <h1 style="margin:0 0 16px;font-size:24px;font-weight:800;color:#09090B;letter-spacing:-.03em">Thank you, {first}.</h1>
        <p style="margin:0 0 16px;color:#6B7280;font-size:15px;line-height:1.65">
          We sincerely appreciate you taking the time to apply for
          <strong style="color:#09090B">{job.title}</strong>
          {f"({job.department})" if job.department else ""}.
        </p>
        <p style="margin:0 0 24px;color:#6B7280;font-size:15px;line-height:1.65">
          After careful review, we have decided to move forward with other candidates whose
          experience more closely matches our current requirements. This was not an easy decision —
          the quality of applications we received was high.
        </p>
        <p style="margin:0 0 24px;color:#6B7280;font-size:15px;line-height:1.65">
          We encourage you to keep an eye on our open roles and apply again in the future.
        </p>
        <p style="margin:0;font-size:13px;color:#9CA3AF;line-height:1.6">
          Thank you again for your interest, and we wish you the very best in your job search.
        </p>
      </td></tr>
      <tr><td style="padding:16px 40px;border-top:1px solid #E5E7EB">
        <p style="margin:0;font-size:11px;color:#C4C4C4">{brand_name} · Built with care in Kigali, Rwanda</p>
      </td></tr>
    </table>
  </td></tr></table>
</body></html>"""
    plain = (
        f"Hi {first},\n\nThank you for applying for {job.title}.\n\n"
        f"After careful review, we've decided to move forward with other candidates "
        f"whose experience more closely matches our current needs.\n\n"
        f"We encourage you to apply again for future roles.\n\n"
        f"Best wishes,\n{brand_name} Recruiting Team"
    )
    return _send(applicant.email, f"Your application for {job.title}", html, plain, brand_name)


def send_shortlist_email(applicant, job, brand_name="Mpact"):
    """Send a shortlist notification to the candidate."""
    if not applicant.email:
        return False
    first = applicant.full_name.split()[0]
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#F5F5F7;font-family:'Inter',system-ui,sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:48px 20px">
    <table width="520" cellpadding="0" cellspacing="0"
           style="background:#fff;border-radius:16px;overflow:hidden;border:1px solid #E5E7EB">
      <tr><td style="background:#09090B;padding:28px 40px">
        <span style="font-size:18px;font-weight:800;color:#fff;letter-spacing:-.025em">{brand_name}</span>
      </td></tr>
      <tr><td style="padding:40px">
        <p style="margin:0 0 4px;font-size:12px;font-weight:700;color:#059669;text-transform:uppercase;letter-spacing:.06em">Great news</p>
        <h1 style="margin:0 0 16px;font-size:24px;font-weight:800;color:#09090B;letter-spacing:-.03em">You've been shortlisted, {first}!</h1>
        <p style="margin:0 0 16px;color:#6B7280;font-size:15px;line-height:1.65">
          We've reviewed your application for <strong style="color:#09090B">{job.title}</strong>
          {f"({job.department})" if job.department else ""} and we're pleased to let you know
          you've been shortlisted for the next stage.
        </p>
        <p style="margin:0 0 24px;color:#6B7280;font-size:15px;line-height:1.65">
          Someone from our team will be in touch shortly with details. If you have questions, just reply to this email.
        </p>
        <div style="background:#ECFDF5;border:1px solid #A7F3D0;border-radius:10px;padding:16px 20px">
          <p style="margin:0;font-size:14px;color:#065F46;font-weight:600">&#10003; Shortlisted for: {job.title}</p>
        </div>
      </td></tr>
      <tr><td style="padding:16px 40px;border-top:1px solid #E5E7EB">
        <p style="margin:0;font-size:11px;color:#C4C4C4">{brand_name} · Built with care in Kigali, Rwanda</p>
      </td></tr>
    </table>
  </td></tr></table>
</body></html>"""
    plain = (
        f"Hi {first},\n\nGreat news! You've been shortlisted for {job.title}.\n\n"
        f"Someone from our team will reach out shortly with next steps.\n\n"
        f"Thank you,\n{brand_name} Recruiting Team"
    )
    return _send(applicant.email, f"You've been shortlisted — {job.title}", html, plain, brand_name)


# ─── recruiter notification ───────────────────────────────────────────────────

def send_new_application_notification(applicant, job, brand_name="Mpact", dashboard_url=""):
    """Notify the recruiter that owns the job when a new application arrives."""
    recruiter = job.recruiter
    if not recruiter or not recruiter.email:
        return False

    ref        = f"MPT-{job.id:04d}-{applicant.id:05d}"
    rec_first  = (recruiter.name or "Recruiter").split()[0]
    total      = job.applicant_count
    exp_line   = f"{applicant.years_experience:.0f} yr{'s' if applicant.years_experience != 1 else ''}" if applicant.years_experience else ""
    loc_line   = applicant.location or ""

    detail_rows = ""
    for label, value in [
        ("Email",      applicant.email),
        ("Location",   loc_line),
        ("Experience", exp_line),
        ("Reference",  ref),
    ]:
        if value:
            detail_rows += (
                f'<tr>'
                f'<td style="padding:5px 0;font-size:13px;color:#9CA3AF;width:38%;vertical-align:top">{label}</td>'
                f'<td style="padding:5px 0;font-size:13px;color:#09090B;font-weight:500">{value}</td>'
                f'</tr>'
            )

    cta_btn = ""
    if dashboard_url:
        cta_btn = (
            f'<table cellpadding="0" cellspacing="0" style="margin-bottom:24px"><tr>'
            f'<td style="border-radius:9px;background:#635BFF;box-shadow:0 4px 12px rgba(99,91,255,.3)">'
            f'<a href="{dashboard_url}" style="display:inline-block;padding:13px 28px;'
            f'font-size:14px;font-weight:700;color:#fff;text-decoration:none">'
            f'Review applicant &rarr;</a></td></tr></table>'
        )

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#F5F5F7;font-family:'Inter',system-ui,sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:48px 20px">
    <table width="520" cellpadding="0" cellspacing="0"
           style="background:#fff;border-radius:16px;overflow:hidden;border:1px solid #E5E7EB">
      <tr><td style="background:#09090B;padding:28px 40px">
        <span style="font-size:18px;font-weight:800;color:#fff;letter-spacing:-.025em">{brand_name}</span>
      </td></tr>
      <tr><td style="padding:40px">
        <p style="margin:0 0 4px;font-size:12px;font-weight:700;color:#635BFF;text-transform:uppercase;letter-spacing:.06em">New Application</p>
        <h1 style="margin:0 0 14px;font-size:24px;font-weight:800;color:#09090B;letter-spacing:-.03em">{applicant.full_name} applied</h1>
        <p style="margin:0 0 20px;color:#6B7280;font-size:15px;line-height:1.65">
          Hi {rec_first}, a new application just arrived for
          <strong style="color:#09090B">{job.title}</strong>.
        </p>
        <div style="background:#F9FAFB;border-radius:10px;padding:16px 20px;margin:0 0 24px;border:1px solid #E5E7EB">
          <table cellpadding="0" cellspacing="0" width="100%">
            {detail_rows}
          </table>
        </div>
        {cta_btn}
        <p style="margin:0;font-size:12px;color:#9CA3AF;line-height:1.6">
          {total} total applicant{"s" if total != 1 else ""} for this role.
        </p>
      </td></tr>
      <tr><td style="padding:16px 40px;border-top:1px solid #E5E7EB">
        <p style="margin:0;font-size:11px;color:#C4C4C4">{brand_name} Recruiter Platform · Kigali, Rwanda</p>
      </td></tr>
    </table>
  </td></tr></table>
</body></html>"""

    plain = (
        f"Hi {rec_first},\n\n"
        f"{applicant.full_name} just applied for {job.title}.\n\n"
        f"Email: {applicant.email}\n"
        f"Reference: {ref}\n"
        f"Total applicants: {total}\n\n"
        + (f"Review: {dashboard_url}\n\n" if dashboard_url else "")
        + f"{brand_name} Recruiting Platform"
    )

    return _send(recruiter.email, f"New application — {job.title}", html, plain, brand_name)
