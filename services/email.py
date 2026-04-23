import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app

logger = logging.getLogger(__name__)


def _build_verification_html(brand: str, name: str, verify_url: str) -> str:
    first = name.split()[0] if name else "there"
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#F5F5F7;font-family:'Inter',system-ui,-apple-system,sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0" style="min-height:100vh">
    <tr><td align="center" style="padding:48px 20px">
      <table width="520" cellpadding="0" cellspacing="0"
             style="background:#ffffff;border-radius:16px;overflow:hidden;
                    border:1px solid #E5E7EB;box-shadow:0 4px 24px rgba(0,0,0,.07)">

        <!-- Brand header -->
        <tr>
          <td style="background:#09090B;padding:28px 40px">
            <table cellpadding="0" cellspacing="0"><tr>
              <td style="width:34px;height:34px;background:#635BFF;border-radius:8px;
                         text-align:center;vertical-align:middle">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
                     stroke="white" stroke-width="2.5" stroke-linecap="round">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </td>
              <td style="padding-left:10px;font-size:18px;font-weight:800;
                         color:#ffffff;letter-spacing:-.025em">{brand}</td>
            </tr></table>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:40px">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;
                      color:#635BFF;letter-spacing:.04em;text-transform:uppercase">
              Email verification
            </p>
            <h1 style="margin:0 0 12px;font-size:26px;font-weight:800;
                       color:#09090B;letter-spacing:-.03em;line-height:1.2">
              Confirm your email<br>to get started
            </h1>
            <p style="margin:0 0 28px;color:#6B7280;font-size:15px;line-height:1.65">
              Hi {first}, you're one step away from screening candidates on {brand}.
              Click the button below to verify your email address and activate your
              recruiter account.
            </p>

            <!-- CTA button -->
            <table cellpadding="0" cellspacing="0" style="margin-bottom:28px">
              <tr>
                <td style="border-radius:9px;background:#635BFF;
                           box-shadow:0 4px 14px rgba(99,91,255,.35)">
                  <a href="{verify_url}"
                     style="display:inline-block;padding:15px 32px;font-size:15px;
                            font-weight:700;color:#ffffff;text-decoration:none;
                            letter-spacing:-.01em">
                    Verify my email &rarr;
                  </a>
                </td>
              </tr>
            </table>

            <p style="margin:0 0 10px;color:#9CA3AF;font-size:13px;line-height:1.6">
              Or paste this link into your browser:
            </p>
            <p style="margin:0;font-size:12px;font-family:'JetBrains Mono',monospace;
                      color:#635BFF;word-break:break-all">
              {verify_url}
            </p>
          </td>
        </tr>

        <!-- Divider info row -->
        <tr>
          <td style="padding:20px 40px;background:#FAFAFA;border-top:1px solid #F0F0F0">
            <table cellpadding="0" cellspacing="0" width="100%"><tr>
              <td style="width:48%;vertical-align:top">
                <p style="margin:0;font-size:12px;color:#9CA3AF;line-height:1.6">
                  <strong style="color:#6B7280">Expires in:</strong> 24 hours
                </p>
              </td>
              <td style="width:4%"></td>
              <td style="width:48%;vertical-align:top;text-align:right">
                <p style="margin:0;font-size:12px;color:#9CA3AF;line-height:1.6">
                  Didn't sign up? Ignore this email.
                </p>
              </td>
            </tr></table>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:16px 40px;border-top:1px solid #E5E7EB">
            <p style="margin:0;font-size:11px;color:#C4C4C4">
              {brand} Recruiter Platform &middot; Built with care in Kigali, Rwanda
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def send_verification_email(to_email: str, to_name: str, verify_url: str) -> bool:
    """Send HTML verification email. Returns True if sent via SMTP, False if SMTP not configured."""
    brand = current_app.config.get("BRAND_NAME", "Mpact")
    html  = _build_verification_html(brand, to_name, verify_url)
    mail_server = current_app.config.get("MAIL_SERVER", "")

    if not mail_server:
        logger.warning("[DEV] SMTP not configured — verification link: %s", verify_url)
        return False

    try:
        from_addr = (
            current_app.config.get("MAIL_FROM")
            or current_app.config.get("MAIL_USERNAME")
            or f"no-reply@mpact.rw"
        )
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Verify your {brand} recruiter account"
        msg["From"]    = f"{brand} <{from_addr}>"
        msg["To"]      = to_email
        msg.attach(MIMEText(html, "html"))

        server = smtplib.SMTP(mail_server, current_app.config.get("MAIL_PORT", 587))
        server.ehlo()
        server.starttls()
        server.login(
            current_app.config["MAIL_USERNAME"],
            current_app.config["MAIL_PASSWORD"],
        )
        server.sendmail(from_addr, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as exc:
        logger.error("Failed to send verification email to %s: %s", to_email, exc)
        return False
