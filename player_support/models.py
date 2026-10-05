from enum import StrEnum

from pydantic import BaseModel, Field


class Queue(StrEnum):
    PLAYER_SUPPORT = "player_support"
    CREATOR_REVIEW = "creator_review"
    TRUST_AND_SAFETY = "trust_and_safety"


class PlayerAsset(BaseModel):
    asset_id: str = Field(min_length=1, max_length=80)
    asset_type: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=1, max_length=120)


class LiveEvent(BaseModel):
    event_id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=120)
    is_live: bool


class ModerationContext(BaseModel):
    queue: Queue
    case_id: str | None = Field(default=None, max_length=80)


class ContactRequest(BaseModel):
    submission_id: str = Field(min_length=1, max_length=80)
    player_email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=254)
    player_name: str = Field(min_length=1, max_length=80)
    message: str = Field(min_length=1, max_length=4000)
    asset: PlayerAsset | None = None
    live_event: LiveEvent | None = None
    moderation: ModerationContext


class ContactReceipt(BaseModel):
    submission_id: str
    queue: Queue
    message_id: str
