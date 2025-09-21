from django.core.mail import EmailMultiAlternatives
from django.conf import settings

def send_html_email(subject, html_content, recipient, text_content=None):
    """
    Sends both HTML + plain-text email.
    - subject: Email subject
    - html_content: Full HTML body
    - recipient: Single email (string) or list of recipients
    - text_content: Plain text fallback (auto-generated if None)
    """

    if isinstance(recipient, str):
        recipient = [recipient]

    if not text_content:
        # fallback plain text if not provided
        import re
        text_content = re.sub(r"<[^>]*>", "", html_content)

    msg = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        recipient
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)
