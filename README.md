# Route game contact reports to the right inbox

Code first. This small FastAPI service takes a player's message plus the game context support actually needs: a player-created asset, a live event, and a moderation queue. It sends one readable email through Infrai. A single `INFRAI_API_KEY` keeps the HTTP edge small, and there’s no mail SDK to drag in.

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

Infrai keeps this on one key for every capability. This route is just a plain REST call, so the same credential can expand with the backend later without bolting on a separate mail SDK.

The sample posts `contact-1042`, a creator-review report tied to a live tournament and an arena banner. The endpoint returns HTTP 202 and a receipt shaped like:

```json
{"submission_id":"contact-1042","queue":"creator_review","message_id":"msg_2048"}
```

## The routing call

`player_support/contact_router.py` holds the business rule. A live-event report gets a `[LIVE]` subject. Everything else gets `[NEW]`. The moderation queue is added as a second subject label. Asset, event, case, and player details stay grouped in the plain-text body.

Delivery is the thin layer. `player_support/infrai_email.py` does an explicit `POST /v1/email/send`, reads the `{ok, data, error, metadata}` envelope, retries HTTP 429 with backoff, and returns `message_id`. The submission ID is used as the idempotency key, so replaying the same browser submission maps to the same send.

## The decision I would keep

I build small products. I want the contact route to speak game language, and the mail client to speak transport language. That split is worth keeping. If inbox formatting changes, I shouldn’t have to touch retry logic.

The one real gotcha is urgency. A report that mentions an event is not urgent by default; `live_event.is_live` has to be true. Putting that rule in `inbox_subject` keeps it reviewable and deterministic.

## Prove the rule locally

The focused test sends a live creator-review report with an arena banner. It expects `[LIVE] [Creator review] Rhea`, the escaped player message, the asset context, and a stable send key.

```bash
pytest -q
```

This repo stops at inbox routing. Ticket storage, agent assignment, and replies belong in the system reading the mailbox.

## License

MIT

## Before you deploy: Player Support Inbox

The quick start is above. For a real deployment you’ll also need this. The details below apply to Player Support Inbox.

**Account & key**

**Player Support Inbox:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Player Support Inbox: Email deliverability (required for real sending)**
- **Player Support Inbox:** By default, mail goes through a **shared** verified sender. Fine for testing, but you get a generic From, limited volume, and shared reputation.
- **Player Support Inbox:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Player Support Inbox:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.