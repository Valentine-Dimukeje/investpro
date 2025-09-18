# core/utils.py
import pycountry

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def country_to_flag(alpha2: str) -> str:
    """Return emoji flag from ISO alpha-2 (e.g. 'US' -> 🇺🇸)."""
    if not alpha2 or len(alpha2) != 2:
        return "🏳️"
    return "".join(chr(0x1F1E6 + ord(c.upper()) - ord('A')) for c in alpha2)

def lookup_country_code(value: str) -> str:
    """
    Accepts many forms: 'US', 'usa', 'United States', 'Ng', 'Nigeria', etc.
    Returns alpha_2 or '' if unknown.
    """
    if not value:
        return ""
    try:
        return pycountry.countries.lookup(value).alpha_2
    except LookupError:
        return ""

# core/utils.py
def send_password_reset_email(user, reset_link):
    subject = "Reset Your Password - Heritage Investment"
    from_email = "heritageinvestmentgrup@gmail.com"  # or settings.DEFAULT_FROM_EMAIL
    to = [user.email]

    html_content = render_to_string("emails/password_reset.html", {
        "user": user,
        "reset_link": reset_link
    })

    email = EmailMultiAlternatives(
        subject,
        "Please use the link to reset your password.",
        from_email,
        to
    )
    email.attach_alternative(html_content, "text/html")
    email.send()
