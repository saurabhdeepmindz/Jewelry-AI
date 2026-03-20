"""SendGrid transactional email client.

Wraps the sendgrid Python SDK for async-compatible use via asyncio.run_in_executor.
Sends single transactional emails and handles webhook signature verification.

Business rules:
- 202 from SendGrid = accepted (not delivered yet)
- Store sg_message_id from X-Message-Id response header
- Webhook signature verified using SENDGRID_WEBHOOK_SECRET
"""
import asyncio
from functools import partial

from src.core.exceptions import SendGridAPIException
from src.core.logging import get_logger

logger = get_logger(__name__)


class SendGridClient:
    """Async-compatible SendGrid transactional email client.

    Uses run_in_executor to wrap the synchronous sendgrid SDK so it integrates
    cleanly with FastAPI and asyncio-based callers.
    """

    def __init__(
        self,
        api_key: str | None = None,
        from_email: str | None = None,
    ) -> None:
        if api_key is None:
            from src.core.config import get_settings
            settings = get_settings()
            api_key = settings.SENDGRID_API_KEY
            from_email = settings.SENDGRID_FROM_EMAIL
        self._api_key = api_key
        self._from_email = from_email

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str | None = None,
    ) -> str:
        """Send a single transactional email. Returns the SendGrid message ID.

        Parameters
        ----------
        to_email:
            Recipient email address.
        subject:
            Email subject line.
        body_html:
            HTML content for the email body.
        body_text:
            Optional plain-text fallback content.

        Returns
        -------
        str
            The X-Message-Id returned by SendGrid (empty string if unavailable).

        Raises
        ------
        SendGridAPIException
            If the SendGrid API call fails or returns an unexpected status code.
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            partial(self._send_sync, to_email, subject, body_html, body_text),
        )
        return result

    def _send_sync(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str | None,
    ) -> str:
        # Lazy import — avoid loading sendgrid at startup when not needed
        import sendgrid
        from sendgrid.helpers.mail import Mail

        sg = sendgrid.SendGridAPIClient(api_key=self._api_key)
        message = Mail(
            from_email=self._from_email,
            to_emails=to_email,
            subject=subject,
            html_content=body_html,
            plain_text_content=body_text or "",
        )
        try:
            response = sg.send(message)
        except Exception as exc:
            raise SendGridAPIException(f"SendGrid send failed: {exc}") from exc

        if response.status_code not in (200, 202):
            raise SendGridAPIException(
                f"SendGrid unexpected status: {response.status_code}"
            )

        # Extract message ID from response headers
        message_id = ""
        if response.headers:
            message_id = response.headers.get("X-Message-Id", "")

        logger.info(
            "SendGrid email sent to=%s message_id=%s",
            to_email,
            message_id,
        )
        return message_id
