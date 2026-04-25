import json
import logging
import smtplib
import ssl
import urllib.error
import urllib.request
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

        <tr>
          <td style="background:#09090B;padding:28px 40px">
            <span style="font-size:18px;font-weight:800;color:#fff;letter-spacing:-.025em">{brand}</span>
          </td>
        </tr>

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
    """
    Send HTML verification email.
    Returns True on success, False if no transport is configured.
    Tries Resend API first, then SMTP.
    """
    brand       = current_app.config.get("BRAND_NAME", "Mpact")
    resend_key  = current_app.config.get("RESEND_API_KEY", "")
    mail_server = current_app.config.get("MAIL_SERVER", "")
    html        = _build_verification_html(brand, to_name, verify_url)
    subject     = f"Verify your {brand} recruiter account"
    first       = to_name.split()[0] if to_name else "there"
    plain       = (
        f"Hi {first},\n\n"
        f"Verify your {brand} recruiter account by visiting:\n{verify_url}\n\n"
        f"This link expires in 24 hours. If you didn't sign up, ignore this email.\n\n"
        f"{brand}"
    )

    from_addr = (
        current_app.config.get("MAIL_FROM")
        or current_app.config.get("MAIL_USERNAME")
        or "no-reply@mpact.rw"
    )

    # ── Resend API ────────────────────────────────────────────────────────────
    if resend_key:
        payload = json.dumps({
            "from":    f"{brand} <{from_addr}>",
            "to":      [to_email],
            "subject": subject,
            "html":    html,
            "text":    plain,
        }).encode()
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=payload,
            headers={
                "Authorization": f"Bearer {resend_key}",
                "Content-Type":  "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read())
                logger.info("[email/resend] Verification sent to %s id=%s", to_email, result.get("id", ""))
                return True
        except urllib.error.HTTPError as exc:
            body = exc.read().decode()
            logger.error("[email/resend] HTTP %s: %s", exc.code, body)
            return False
        except Exception as exc:
            logger.error("[email/resend] %s", exc)
            return False

    # ── SMTP ──────────────────────────────────────────────────────────────────
    if mail_server:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = f"{brand} <{from_addr}>"
            msg["To"]      = to_email
            msg.attach(MIMEText(plain, "plain"))
            msg.attach(MIMEText(html,  "html"))

            port = int(current_app.config.get("MAIL_PORT", 587))
            username = current_app.config.get("MAIL_USERNAME", "")
            password = current_app.config.get("MAIL_PASSWORD", "")
            print(f"[email/smtp] Connecting to {mail_server}:{port} as {username}", flush=True)
            ctx = ssl.create_default_context()
            if port == 465:
                server = smtplib.SMTP_SSL(mail_server, port, timeout=30, context=ctx)
            else:
                server = smtplib.SMTP(mail_server, port, timeout=30)
                server.ehlo()
                server.starttls(context=ctx)
                server.ehlo()
            server.login(username, password)
            server.sendmail(from_addr, to_email, msg.as_string())
            server.quit()
            print(f"[email/smtp] ✓ Verification sent to {to_email}", flush=True)
            return True
        except smtplib.SMTPAuthenticationError as exc:
            print(f"[email/smtp] ✗ AUTH FAILED — check MAIL_USERNAME/MAIL_PASSWORD: {exc}", flush=True)
            return False
        except smtplib.SMTPException as exc:
            print(f"[email/smtp] ✗ SMTP error: {exc}", flush=True)
            return False
        except Exception as exc:
            print(f"[email/smtp] ✗ Unexpected error: {type(exc).__name__}: {exc}", flush=True)
            return False

    print("[email] No transport configured (RESEND_API_KEY and MAIL_SERVER both empty)", flush=True)
    logger.warning("[DEV] No email transport — verification link: %s", verify_url)
    return False
