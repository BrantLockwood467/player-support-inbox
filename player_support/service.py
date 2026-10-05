import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Request

from player_support.contact_router import route_contact
from player_support.infrai_email import InfraiEmail, InfraiError
from player_support.models import ContactReceipt, ContactRequest


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    api_key = os.environ.get("INFRAI_API_KEY")
    team_inbox = os.environ.get("TEAM_INBOX")
    if not api_key or not team_inbox:
        raise RuntimeError("INFRAI_API_KEY and TEAM_INBOX are required")
    app.state.infrai_email = InfraiEmail(api_key)
    app.state.team_inbox = team_inbox
    yield
    await app.state.infrai_email.close()


app = FastAPI(title="Player support inbox", lifespan=lifespan)


@app.post("/contact", response_model=ContactReceipt, status_code=202)
async def submit_contact(contact: ContactRequest, request: Request) -> ContactReceipt:
    try:
        return await route_contact(
            contact,
            request.app.state.team_inbox,
            request.app.state.infrai_email,
        )
    except InfraiError as exc:
        caller_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=caller_status,
            detail={"code": exc.code, "error": exc.detail},
        ) from exc

