from app.core.config import settings


async def send_email(to: str, subject: str, body: str) -> None:
    """
    Single wrapper for all outgoing email — currently a stub that logs to console.
    Swap in a real provider (SendGrid, AWS SES, Postmark) here when ready; nothing
    else in the app needs to change since every caller goes through this function.
    """
    if not settings.smtp_configured:
        print(f"[email:stub] to={to} subject='{subject}'\n{body}")
        return

    # Example wiring for a real provider would go here, e.g.:
    # await send_via_ses(to, subject, body)
    raise NotImplementedError("Configure a real email provider in services/email.py")


def build_reset_password_email(reset_token: str) -> tuple[str, str]:
    reset_link = f"{settings.frontend_origin}/reset-password?token={reset_token}"
    subject = "Reset your MedStock password"
    body = (
        f"Click the link below to reset your password. This link expires in 30 minutes.\n\n"
        f"{reset_link}\n\n"
        f"If you didn't request this, you can safely ignore this email."
    )
    return subject, body
