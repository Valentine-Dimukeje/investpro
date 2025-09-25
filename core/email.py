import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from django.conf import settings

def send_brevo_email(subject, html_content, to_email, to_name=""):
    """
    Send email using Brevo API
    """
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = settings.BREVO_API_KEY  

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

    sender = {"name": settings.DEFAULT_FROM_NAME, "email": settings.DEFAULT_FROM_EMAIL}
    to = [{"email": to_email, "name": to_name or to_email}]

    email = sib_api_v3_sdk.SendSmtpEmail(
        to=to,
        html_content=html_content,
        subject=subject,
        sender=sender,
    )

    try:
        response = api_instance.send_transac_email(email)
        return {"success": True, "response": response}
    except ApiException as e:
        return {"success": False, "error": str(e)}
