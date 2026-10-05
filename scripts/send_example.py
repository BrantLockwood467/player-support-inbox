import json
import urllib.request


payload = {
    "submission_id": "contact-1042",
    "player_email": "rhea@example.com",
    "player_name": "Rhea",
    "message": "My arena banner is stuck in review during tonight's tournament.",
    "asset": {
        "asset_id": "banner-88",
        "asset_type": "arena_banner",
        "title": "Neon Finals",
    },
    "live_event": {
        "event_id": "tournament-7",
        "name": "Friday Finals",
        "is_live": True,
    },
    "moderation": {"queue": "creator_review", "case_id": "case-31"},
}

request = urllib.request.Request(
    "http://127.0.0.1:8000/contact",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(request) as response:
    print(response.read().decode())

