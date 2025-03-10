from constance import config as constance_config
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user

        if (
            not user.is_authenticated
            or user.is_staff
            or user.is_superuser
            or request.method != "GET"
            or request.path_info.startswith(("/i18n", "/admin", "/explorer"))
            or not constance_config.ENABLE_REDIRECT_MIDDLEWARE
        ):
            response = self.get_response(request)
            return response

        from django.http import HttpResponseRedirect
        from django.urls import reverse
        from django.contrib import messages
        from django.utils.translation import gettext_lazy as _

        msgs = {messages.WARNING: [], messages.INFO: []}
        redirect_url = None
        account = getattr(user, "account", None)

        if not account:
            msgs[messages.INFO].append(_("You do not have an account."))

        elif not getattr(account, "selected_tenant_company_id", None):
            msgs[messages.WARNING].append(
                _("You do not have a company associated with your account.")
            )
            msgs[messages.INFO].append(_("You can create a company from this page."))
            redirect_url = reverse("create-company")

        is_current_path_equal_to_redirect = request.path == redirect_url

        for tag, mlst in msgs.items():
            for m in mlst:
                if not is_current_path_equal_to_redirect:
                    messages.add_message(request, tag, m)

        if redirect_url and not is_current_path_equal_to_redirect:
            return HttpResponseRedirect(redirect_url)

        response = self.get_response(request)
        return response


class LoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        << Request Headers >>
        HTTP_ACCEPT                # Media types the client can accept
        HTTP_ACCEPT_ENCODING       # Encodings the client can handle (e.g., gzip)
        HTTP_ACCEPT_LANGUAGE       # Preferred languages for the response
        HTTP_AUTHORIZATION         # Credentials for authenticating the client
        HTTP_CACHE_CONTROL         # Directives for caching mechanisms
        HTTP_CONNECTION            # Control over the connection's persistence
        HTTP_CONTENT_LENGTH        # Size of the request body in bytes
        HTTP_CONTENT_TYPE          # Media type of the request body
        HTTP_COOKIE                # Cookies sent from the client to the server
        HTTP_HOST                  # Domain name and port number of the server
        HTTP_IF_MODIFIED_SINCE     # Makes the request conditional based on modification date
        HTTP_IF_NONE_MATCH         # Makes the request conditional based on ETag
        HTTP_IF_RANGE              # Makes the request conditional based on an ETag or date
        HTTP_IF_UNMODIFIED_SINCE   # Makes the request conditional based on unmodified date
        HTTP_RANGE                 # Specifies a byte range for partial content requests
        HTTP_REFERER               # URL of the referring page
        HTTP_TE                    # Transfer encodings the client accepts
        HTTP_USER_AGENT            # Information about the client software
        HTTP_X_FORWARDED_FOR       # Lists the originating IP addresses of a client behind proxies or load balancers
        HTTP_X_FORWARDED_PROTO     # Indicates the protocol (HTTP or HTTPS) used by the client
        HTTP_X_REQUESTED_WITH      # Identifies Ajax requests (e.g., XMLHttpRequest)
        HTTP_X_FORWARDED_HOST      # Original host requested by the client in the Host HTTP request header
        HTTP_X_FORWARDED_PORT      # Port of the original request made by the client
        """

        """
        << Response Headers >>
        Access-Control-Allow-Origin       # Permitted origins for cross-origin requests
        Access-Control-Allow-Methods      # Allowed HTTP methods for cross-origin requests
        Access-Control-Allow-Headers      # Allowed headers for cross-origin requests
        Access-Control-Allow-Credentials  # Whether credentials are allowed in cross-origin requests
        Access-Control-Expose-Headers     # Headers that can be exposed to the client in cross-origin responses
        Access-Control-Max-Age            # Time to cache preflight request responses
        Content-Encoding                  # Encoding applied to the response body
        Content-Length                    # Size of the response body in bytes
        Content-Type                      # Media type of the response body
        Date                              # Date and time when the response was generated
        ETag                              # Unique identifier for the resource version
        Expires                           # Date/time after which the response is considered stale
        Last-Modified                     # Date/time when the resource was last modified
        Location                          # Redirects the client to a different URL
        Retry-After                       # Time to wait before making a follow-up request
        Server                            # Information about the server
        WWW-Authenticate                  # Authentication challenges (e.g., Basic, Digest)
        X-Content-Type-Options            # Prevents MIME type sniffing
        X-Frame-Options                   # Prevents the page from being displayed in a frame
        X-XSS-Protection                  # Enables or disables cross-site scripting (XSS) protection
        X-Content-Duration                # Indicates the length of time in seconds that the response content is intended to be valid
        X-Permitted-Cross-Domain-Policies  # Controls the cross-domain policy for Flash and other client-side technologies
        """

        """Log request details"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if x_forwarded_for:
            x_forwarded_for = x_forwarded_for.split(",")[0]

        request_log = {
            "host": request.META.get("HTTP_HOST", ""),
            "x_forwarded_for": x_forwarded_for,
            "remote_addr": request.META.get("REMOTE_ADDR", ""),
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "referer": request.META.get("HTTP_REFERER", ""),
            "time": datetime.now().isoformat(),
            "username": request.user.username if request.user.is_authenticated else "",
            "user_id": request.user.id if request.user.is_authenticated else "",
        }
        request.session["request_log"] = request_log
        request.session.save()

        """Process the request"""
        response = self.get_response(request)

        """Log response details"""
        response_log = {
            "status_code": response.status_code,
            "time": datetime.now().isoformat(),
        }

        """Merge logs"""
        log = {
            "request_log": request_log,
            "response_log": response_log,
        }
        if constance_config.ENABLE_LOGGING_MIDDLEWARE_DUMPS:
            import json

            logger.info(json.dumps(log))

        return response
