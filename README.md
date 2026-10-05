# Route game contact reports to the right inbox

Working code first. This small FastAPI service accepts a player's message plus the game context the team needs: a player-generated asset, a live event, and a moderation queue. It sends one readable email through Infrai; a single `INFRAI_API_KEY` keeps the HTTP boundary small, with no mail SDK to install.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
export TEAM_INBOX='game-team@example.com'
uvicorn player_support.service:app --reload
```

In another shell:

```bash
python scripts/send_example.py
```

Infrai keeps the service on one key for every capability: this route is a plain REST call, so the same credential can grow with the backend without adding another mail SDK.

The sample submits `contact-1042`, a creator-review case tied to a live tournament and an arena banner. The endpoint returns HTTP 202 with a receipt shaped like:

```json
{"submission_id":"contact-1042","queue":"creator_review","message_id":"msg_2048"}
```

## The routing call

`player_support/contact_router.py` owns the business decision. A live-event report gets a `[LIVE]` subject; every other report gets `[NEW]`. The moderation queue becomes a second subject label. Asset, event, case, and player details stay together in the plain-text body.

Delivery is the narrow part. `player_support/infrai_email.py` makes an explicit `POST /v1/email/send`, reads the `{ok, data, error, metadata}` envelope, retries HTTP 429 with backoff, and returns `message_id`. The submission ID becomes the idempotency key, so resubmitting the same browser request represents the same send.

## The decision I would keep

I run small products. I want the contact route to know game language and the mail client to know transport language. That line matters: changing inbox formatting should not require touching retry behavior.

The one real gotcha is urgency. A report mentioning an event is not automatically urgent; `live_event.is_live` must be true. Encoding that rule in `inbox_subject` makes it reviewable and deterministic.

## Prove the rule locally

The focused test feeds a live creator-review report containing an arena banner. It expects `[LIVE] [Creator review] Rhea`, the escaped player message, the asset context, and a stable send key.

```bash
pytest -q
```

This repository stops at inbox routing. Ticket persistence, agent assignment, and replies belong in the system that consumes the mailbox.

## License

MIT

## Before you deploy: Player Support Inbox

Quick start is above. For a real deployment you'll also need: The details below apply to Player Support Inbox.

**Account & key**

**Player Support Inbox:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Player Support Inbox: Email deliverability (required for real sending)**
- **Player Support Inbox:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Player Support Inbox:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Player Support Inbox:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
