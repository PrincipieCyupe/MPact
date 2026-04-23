"""
Email notifications for recruiting events.
Requires MAIL_* env vars. Fails silently when unconfigured.
"""
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import Config


def _smtp_configured():
    return bool(Config.MAIL_SERVER and Config.MAIL_USERNAME and Config.MAIL_PASSWORD)


def send_shortlist_email(applicant, job, brand_name="Mpact"):
    """Send a shortlist notification to the candidate."""
    if not _smtp_configured():
        print(f"[email] SMTP not configured — skipping email to {applicant.email}", flush=True)
        return False

    subject = f"Your application for {job.title} — Update"

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f6f6f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f6f6f6;padding:40px 20px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.08);">

        <!-- Header -->
        <tr>
          <td style="padding:32px 40px 24px;border-bottom:1px solid #f0f0f0;">
            <span style="font-size:18px;font-weight:700;color:#111;letter-spacing:-0.3px">{brand_name}</span>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:36px 40px;">
            <h2 style="margin:0 0 20px;font-size:22px;font-weight:600;color:#111;letter-spacing:-0.3px;">
              Good news, {applicant.full_name.split()[0]}
            </h2>
            <p style="margin:0 0 16px;color:#444;font-size:15px;line-height:1.65;">
              We've reviewed your application for <strong style="color:#111">{job.title}</strong>
              {f'({job.department})' if job.department else ''} and we're pleased to let you know
              that you've been shortlisted for the next stage of our selection process.
            </p>
            <p style="margin:0 0 16px;color:#444;font-size:15px;line-height:1.65;">
              Someone from our team will reach out to you soon with details on the next steps.
              In the meantime, if you have any questions, just reply to this email.
            </p>
            <p style="margin:0 0 28px;color:#444;font-size:15px;line-height:1.65;">
              Thank you for your time and interest — we look forward to speaking with you.
            </p>
            <table cellpadding="0" cellspacing="0">
              <tr>
                <td style="background:#111;border-radius:6px;padding:12px 24px;">
                  <span style="color:#fff;font-size:14px;font-weight:600;">Application: {job.title}</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:24px 40px;border-top:1px solid #f0f0f0;background:#fafafa;">
            <p style="margin:0;color:#999;font-size:12px;line-height:1.5;">
              This message was sent by the {brand_name} recruiting team.<br>
              You are receiving this because you applied for a position through our platform.
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""

    plain = (
        f"Hi {applicant.full_name.split()[0]},\n\n"
        f"We've reviewed your application for {job.title} and you've been shortlisted "
        f"for the next stage of our selection process.\n\n"
        f"Someone will be in touch with you shortly.\n\n"
        f"Thank you,\n{brand_name} Recruiting Team"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{brand_name} Recruiting <{Config.MAIL_USERNAME}>"
    msg["To"] = applicant.email
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        context = ssl.create_default_context()
        port = int(Config.MAIL_PORT or 587)
        if port == 465:
            with smtplib.SMTP_SSL(Config.MAIL_SERVER, port, context=context) as server:
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.sendmail(Config.MAIL_USERNAME, applicant.email, msg.as_string())
        else:
            with smtplib.SMTP(Config.MAIL_SERVER, port) as server:
                server.ehlo()
                server.starttls(context=context)
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.sendmail(Config.MAIL_USERNAME, applicant.email, msg.as_string())
        print(f"[email] ✓ Shortlist email sent to {applicant.email}", flush=True)
        return True
    except Exception as exc:
        print(f"[email] ✗ Failed to send to {applicant.email}: {exc}", flush=True)
        return False
