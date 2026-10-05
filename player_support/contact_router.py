from html import escape
from typing import Any

from player_support.models import ContactReceipt, ContactRequest, Queue


QUEUE_LABELS = {
    Queue.PLAYER_SUPPORT: "Player support",
    Queue.CREATOR_REVIEW: "Creator review",
    Queue.TRUST_AND_SAFETY: "Trust and safety",
}


def inbox_subject(contact: ContactRequest) -> str:
    priority = "LIVE" if contact.live_event and contact.live_event.is_live else "NEW"
    return f"[{priority}] [{QUEUE_LABELS[contact.moderation.queue]}] {contact.player_name}"


def inbox_text(contact: ContactRequest) -> str:
    lines = [
        f"Submission: {contact.submission_id}",
        f"Player: {contact.player_name} <{contact.player_email}>",
        f"Queue: {contact.moderation.queue.value}",
    ]
    if contact.moderation.case_id:
        lines.append(f"Moderation case: {contact.moderation.case_id}")
    if contact.asset:
        lines.append(
            f"Player asset: {contact.asset.asset_type} / {contact.asset.title} "
            f"({contact.asset.asset_id})"
        )
    if contact.live_event:
        state = "live" if contact.live_event.is_live else "scheduled"
        lines.append(
            f"Live event: {contact.live_event.name} ({contact.live_event.event_id}, {state})"
        )
    lines.extend(["", "Player message:", escape(contact.message, quote=False)])
    return "\n".join(lines)


async def route_contact(
    contact: ContactRequest, team_inbox: str, email: Any
) -> ContactReceipt:
    message_id = await email.send(
        to=team_inbox,
        subject=inbox_subject(contact),
        text=inbox_text(contact),
        idempotency_key=f"game-contact-{contact.submission_id}",
    )
    return ContactReceipt(
        submission_id=contact.submission_id,
        queue=contact.moderation.queue,
        message_id=message_id,
    )
