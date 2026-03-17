from user_agents import parse as ua_parse

from djangocms_ab_testing.models import ABCounter

COOKIE_NAME_PREFIX = "ab_variant_"
COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days


def get_ab_variant(request, test_name, variant_keys):
    """
    Get the variant for this request. Checks cookie first, then round-robin.
    Queues the cookie to be set in the response via middleware.
    """
    cookie_name = COOKIE_NAME_PREFIX + test_name
    variant_key = request.COOKIES.get(cookie_name)

    if variant_key and variant_key in variant_keys:
        return variant_key

    # Assign via round-robin
    variant_key = ABCounter.next_variant(test_name, list(variant_keys))

    # Queue cookie to be set by middleware
    if not hasattr(request, '_ab_cookies_to_set'):
        request._ab_cookies_to_set = {}
    request._ab_cookies_to_set[cookie_name] = variant_key

    return variant_key


def get_device_info(request):
    """Parse device info from User-Agent header."""
    ua_string = request.META.get('HTTP_USER_AGENT', '')
    ua = ua_parse(ua_string)
    return {
        'device_type': 'mobile' if ua.is_mobile else ('tablet' if ua.is_tablet else 'desktop'),
        'browser': str(ua.browser.family),
        'browser_version': str(ua.browser.version_string),
        'os': str(ua.os.family),
        'os_version': str(ua.os.version_string),
        'is_bot': ua.is_bot,
    }
