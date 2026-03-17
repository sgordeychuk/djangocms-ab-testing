import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from djangocms_ab_testing.models import ABEvent, ABTest
from djangocms_ab_testing.ab_utils import get_device_info
from djangocms_ab_testing.conf import get_valid_actions


@csrf_protect
@require_POST
def ab_event_view(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    variant = data.get("variant", "")
    action = data.get("action", "")
    client_meta = data.get("meta", {})
    test_name = data.get("test_name", "")

    if not variant or len(variant) > 2:
        return JsonResponse({"error": "Invalid variant"}, status=400)
    if action not in get_valid_actions():
        return JsonResponse({"error": "Invalid action"}, status=400)

    ab_test = ABTest.objects.filter(slug=test_name).first()
    if not ab_test:
        return JsonResponse({"error": "Unknown test"}, status=400)

    # Merge client meta with server-side device info
    server_meta = get_device_info(request)
    meta = {**server_meta, **client_meta}

    session_key = request.session.session_key or ""
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    ABEvent.objects.create(
        test=ab_test,
        variant=variant,
        action=action,
        session_key=session_key,
        meta=meta,
    )

    return JsonResponse({"status": "ok"})
