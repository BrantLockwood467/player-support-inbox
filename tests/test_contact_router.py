import asyncio

from player_support.contact_router import route_contact
from player_support.models import ContactRequest, Queue


class RecordingEmail:
    def __init__(self) -> None:
        self.sent: dict[str, str] = {}

    async def send(self, **message: str) -> str:
        self.sent = message
        return "msg_2048"


def test_live_creator_report_is_visible_and_repeat_safe() -> None:
    contact = ContactRequest.model_validate(
        {
            "submission_id": "contact-1042",
            "player_email": "rhea@example.com",
            "player_name": "Rhea",
            "message": "Please check <this> banner.",
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
    )
    email = RecordingEmail()

    receipt = asyncio.run(route_contact(contact, "team@example.com", email))

    assert email.sent["subject"] == "[LIVE] [Creator review] Rhea"
    assert email.sent["idempotency_key"] == "game-contact-contact-1042"
    assert "Player asset: arena_banner / Neon Finals (banner-88)" in email.sent["text"]
    assert "Please check &lt;this&gt; banner." in email.sent["text"]
    assert receipt.queue is Queue.CREATOR_REVIEW
    assert receipt.message_id == "msg_2048"
