from djangocms_ab_testing.ab_utils import COOKIE_MAX_AGE


class ABCookieMiddleware:
    """Sets queued A/B cookies on the response and disables page cache for AB-tested pages."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        cookies_to_set = getattr(request, '_ab_cookies_to_set', {})
        if cookies_to_set:
            for cookie_name, variant_key in cookies_to_set.items():
                response.set_cookie(
                    cookie_name,
                    variant_key,
                    max_age=COOKIE_MAX_AGE,
                    httponly=False,
                    samesite='Lax',
                )
            response['Cache-Control'] = 'private, no-store'

        return response
