from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    Session auth without CSRF check for API requests from SPA (localhost:5173).
    Do NOT use for public, unsecured deployments.
    """

    def enforce_csrf(self, request):
        return

