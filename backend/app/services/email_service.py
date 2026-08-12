import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from backend.app.config import settings

logger = logging.getLogger("jobpulse.email")

class EmailService:
    @classmethod
    def is_smtp_configured(cls) -> bool:
        return bool(settings.SMTP_HOST and settings.SMTP_HOST.strip())

    @classmethod
    def _send_email(cls, recipient: str, subject: str, body_text: str, body_html: Optional[str] = None) -> bool:
        if not cls.is_smtp_configured():
            logger.info(f"[EMAIL MOCK] To: {recipient} | Subject: {subject}\n{body_text}")
            print(f"[EMAIL MOCK] To: {recipient} | Subject: {subject} | Body: {body_text[:100]}...")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
            msg["To"] = recipient

            part1 = MIMEText(body_text, "plain")
            msg.attach(part1)

            if body_html:
                part2 = MIMEText(body_html, "html")
                msg.attach(part2)

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                server.starttls()
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(settings.EMAIL_FROM, [recipient], msg.as_string())
            
            logger.info(f"[EMAIL DISPATCHED] To: {recipient} | Subject: {subject}")
            return True
        except Exception as e:
            logger.error(f"[EMAIL ERROR] Failed to send email to {recipient}: {e}")
            print(f"[EMAIL ERROR] Failed to send email to {recipient}: {e}")
            return False

    @classmethod
    def send_verification_email(cls, recipient: str, verification_link: str) -> bool:
        subject = "Verify your JobPulse account"
        text = f"Welcome to JobPulse!\n\nPlease verify your email address by clicking the link below:\n{verification_link}\n\nThis link expires in {settings.VERIFICATION_TOKEN_EXPIRY_HOURS} hours.\nIf you did not create an account, please ignore this email."
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #333; background: #0f172a; color: #f8fafc; border-radius: 8px;">
            <h2 style="color: #38bdf8;">Welcome to JobPulse</h2>
            <p>Please click the button below to verify your email address and activate your account:</p>
            <p style="margin: 30px 0;">
                <a href="{verification_link}" style="background-color: #38bdf8; color: #0f172a; font-weight: bold; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Verify Email Address</a>
            </p>
            <p style="font-size: 12px; color: #94a3b8;">Or copy and paste this link in your browser:<br>{verification_link}</p>
            <p style="font-size: 12px; color: #64748b; margin-top: 30px;">Expires in {settings.VERIFICATION_TOKEN_EXPIRY_HOURS} hours.</p>
        </div>
        """
        return cls._send_email(recipient, subject, text, html)

    @classmethod
    def send_otp_email(cls, recipient: str, otp_code: str) -> bool:
        subject = f"Your JobPulse Verification Code: {otp_code}"
        text = f"Your JobPulse verification code is: {otp_code}\n\nThis code expires in {settings.OTP_EXPIRY_MINUTES} minutes.\nNever share this code with anyone."
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #333; background: #0f172a; color: #f8fafc; border-radius: 8px;">
            <h2 style="color: #38bdf8;">Verification Code</h2>
            <p>Use the 6-digit code below to authenticate your request:</p>
            <div style="background: #1e293b; padding: 15px; border-radius: 6px; text-align: center; font-size: 28px; font-weight: bold; letter-spacing: 5px; color: #38bdf8; margin: 20px 0;">
                {otp_code}
            </div>
            <p style="font-size: 12px; color: #94a3b8;">This code expires in {settings.OTP_EXPIRY_MINUTES} minutes.</p>
        </div>
        """
        return cls._send_email(recipient, subject, text, html)

    @classmethod
    def send_password_reset_email(cls, recipient: str, reset_link: str) -> bool:
        subject = "Reset your JobPulse password"
        text = f"You requested a password reset for your JobPulse account.\n\nClick the link below to set a new password:\n{reset_link}\n\nIf you did not request this password reset, please ignore this email."
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #333; background: #0f172a; color: #f8fafc; border-radius: 8px;">
            <h2 style="color: #38bdf8;">Password Reset Request</h2>
            <p>Click the button below to reset your JobPulse password:</p>
            <p style="margin: 30px 0;">
                <a href="{reset_link}" style="background-color: #f43f5e; color: #ffffff; font-weight: bold; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Reset Password</a>
            </p>
            <p style="font-size: 12px; color: #94a3b8;">Or copy and paste this link in your browser:<br>{reset_link}</p>
        </div>
        """
        return cls._send_email(recipient, subject, text, html)
