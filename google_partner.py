"""
google_partner.py

PLACEHOLDER for a future, LEGITIMATE Google Partner / Subscription API
integration. This file intentionally contains no working logic yet.

IMPORTANT — READ BEFORE USING:

1. This system's own activation links (https://<your-domain>/activate/<token>)
   are completely separate from Google's managed activation flow at
   serviceactivation.google.com. You cannot make a custom token work on
   a google.com URL — that domain and its tokens are controlled entirely
   by Google's own infrastructure.

2. If your service is a Google Workspace / Google Cloud / Google Play
   partner offering that needs to interoperate with Google's activation
   or subscription systems, that requires:
     - Enrollment in the relevant Google Partner Program
     - OAuth2 credentials issued by Google for your partner account
     - Use of Google's official client libraries / REST APIs
       (e.g. Google Workspace Reseller API, Cloud Channel API,
       Play Developer API — whichever applies to your product)
   None of that can be reproduced, faked, or bypassed with a custom
   token generator. This file exists so that, once you have real
   Google Partner credentials, the integration has an obvious place
   to live without touching the rest of the codebase.

3. Until you have those credentials, the system works entirely on your
   own domain and your own database — no Google integration is required
   for it to function.

--------------------------------------------------------------------
Suggested structure once you have real credentials (all TODOs):
--------------------------------------------------------------------
"""

# from google.oauth2 import service_account
# from googleapiclient.discovery import build

# TODO: load credentials from a secure location (never hardcode).
# GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")


class GooglePartnerClient:
    """
    Placeholder client. Fill in once you are enrolled in the relevant
    Google Partner program and have valid, legitimately-issued credentials.
    """

    def __init__(self, credentials_path: str | None = None):
        self.credentials_path = credentials_path
        self.enabled = bool(credentials_path)

    def is_configured(self) -> bool:
        return self.enabled

    def create_subscription_activation(self, *args, **kwargs):
        """
        TODO: Implement using the official Google API client once
        partner credentials are available. This must call Google's
        real API — it must never construct or imitate a
        serviceactivation.google.com URL locally.
        """
        raise NotImplementedError(
            "Google Partner integration is not configured. "
            "This system currently runs entirely on your own domain."
        )


# Default instance — inert until real credentials are supplied.
google_partner_client = GooglePartnerClient(credentials_path=None)
