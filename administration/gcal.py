import logging
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction

# Google Calendar integration deps
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request as GoogleRequest
except Exception:  # pragma: no cover - optional at import time
    Credentials = None
    Flow = None
    build = None
    GoogleRequest = None

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
]


def _get_google_client_config():
    client_config = getattr(settings, "GOOGLE_OAUTH_CLIENT_CONFIG", None)
    if not client_config or not isinstance(client_config, dict) or "web" not in client_config:
        raise RuntimeError("GOOGLE_OAUTH_CLIENT_CONFIG is not configured in settings")
    return client_config


def _serialize_credentials(creds):
    return {
        "token": getattr(creds, "token", None),
        "refresh_token": getattr(creds, "refresh_token", None),
        "token_uri": getattr(creds, "token_uri", None),
        "client_id": getattr(creds, "client_id", None),
        "client_secret": getattr(creds, "client_secret", None),
        "scopes": getattr(creds, "scopes", None),
        "expiry": creds.expiry.isoformat() if getattr(creds, "expiry", None) else None,
    }


def _credentials_from_json(json_str: str):
    if not Credentials:
        return None
    import json as _json
    data = _json.loads(json_str)
    creds = Credentials(
        token=data.get("token"),
        refresh_token=data.get("refresh_token"),
        token_uri=data.get("token_uri"),
        client_id=data.get("client_id"),
        client_secret=data.get("client_secret"),
        scopes=data.get("scopes"),
    )
    return creds


@login_required
def google_oauth_start(request):
    if Flow is None:
        return JsonResponse({"error": "Google libraries not installed"}, status=500)
    client_config = _get_google_client_config()
    redirect_uri = client_config["web"].get("redirect_uris", [None])[0]
    flow = Flow.from_client_config(client_config, scopes=SCOPES)
    flow.redirect_uri = redirect_uri
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    request.session["google_oauth_state"] = state
    return redirect(authorization_url)


@login_required
def google_oauth_callback(request):
    if Flow is None:
        return JsonResponse({"error": "Google libraries not installed"}, status=500)
    client_config = _get_google_client_config()
    redirect_uri = client_config["web"].get("redirect_uris", [None])[0]
    state = request.session.get("google_oauth_state")
    flow = Flow.from_client_config(client_config, scopes=SCOPES, state=state)
    flow.redirect_uri = redirect_uri
    try:
        flow.fetch_token(authorization_response=request.build_absolute_uri())
    except Exception:  # pragma: no cover
        logger.exception("Failed to fetch Google OAuth token")
        messages.error(request, "Failed to connect Google account.")
        return redirect("administration:schedule")
    creds = flow.credentials
    import json as _json
    profile = request.user.profile
    creds_json = _json.dumps(_serialize_credentials(creds))
    logger.info("[gcal] Storing Google creds for profile_id=%s", getattr(profile, 'id', None))
    with transaction.atomic():
        # Use update() to guarantee a DB write even if a stale instance is in memory
        type(profile).objects.filter(pk=profile.pk).update(
            google_credentials_json=creds_json,
            google_sync_enabled=True,
        )
    messages.success(request, "Google Calendar connected.")
    return redirect("administration:schedule")


@login_required
def google_oauth_disconnect(request):
    profile = request.user.profile
    with transaction.atomic():
        type(profile).objects.filter(pk=profile.pk).update(
            google_sync_enabled=False,
            google_credentials_json=None,
        )
    messages.info(request, "Google Calendar disconnected.")
    return redirect("administration:schedule")


@login_required
def google_events(request):
    if build is None or Credentials is None:
        return JsonResponse([], safe=False)
    profile = request.user.profile
    if not (profile.google_sync_enabled and profile.google_credentials_json):
        return JsonResponse([], safe=False)
    creds = _credentials_from_json(profile.google_credentials_json)
    # Refresh if needed
    try:
        if creds and hasattr(creds, "expired") and creds.expired and getattr(creds, "refresh_token", None) and GoogleRequest is not None:
            creds.refresh(GoogleRequest())
            import json as _json
            profile.google_credentials_json = _json.dumps(_serialize_credentials(creds))
            profile.save(update_fields=["google_credentials_json"])
    except Exception:  # pragma: no cover
        logger.exception("Failed to refresh Google credentials")
        return JsonResponse([], safe=False)
    service = build("calendar", "v3", credentials=creds, cache_discovery=False)
    time_min = request.GET.get("start")
    time_max = request.GET.get("end")
    tz = request.GET.get("tz") or getattr(settings, "TIME_ZONE", "UTC")
    events = []
    page_token = None
    while True:
        resp = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
            timeZone=tz,
            pageToken=page_token,
        ).execute()
        for ev in resp.get("items", []):
            start = ev.get("start", {})
            end = ev.get("end", {})
            all_day = "date" in start or "date" in end
            events.append({
                "id": ev.get("id"),
                "title": ev.get("summary") or "(No title)",
                "start": start.get("dateTime") or start.get("date"),
                "end": end.get("dateTime") or end.get("date"),
                "allDay": all_day,
                "url": ev.get("htmlLink"),
            })
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return JsonResponse(events, safe=False)
