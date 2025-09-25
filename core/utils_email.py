# core/utils/email.py
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from django.conf import settings


def send_brevo_email(subject, html_content, to_email, to_name=""):
    """
    Send transactional email via Brevo
    """
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = settings.BREVO_API_KEY

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    sender = {"name": "Heritage Investment", "email": "no-reply@heritageinvestmentgrup.com"}
    to = [{"email": to_email, "name": to_name or to_email}]

    email = sib_api_v3_sdk.SendSmtpEmail(
        to=to,
        sender=sender,
        subject=subject,
        html_content=html_content
    )

    try:
        response = api_instance.send_transac_email(email)
        return response
    except ApiException as e:
        raise Exception(f"Brevo email failed: {e}")
