# Medical Store Backend

FastAPI backend for the Medical Store module — inventory, rule-based restock prediction,
WhatsApp supplier ordering, invoicing, and profit & loss reporting.

## Stack

- FastAPI + Uvicorn
- PostgreSQL (works with any provider — Neon free tier recommended for dev, see below)
- SQLAlchemy 2.0 + Alembic migrations
- JWT auth (access token + httpOnly refresh cookie)
- APScheduler for the Friday restock-prediction job
- WeasyPrint for GST invoice PDF generation

## 1. Get a free database (Neon)

1. Go to https://neon.tech, sign up free, create a project.
2. Copy the connection string it gives you (looks like `postgresql://user:pass@ep-xxx.neon.tech/dbname`).
3. Paste it into `.env` as `DATABASE_URL`.

## 2. Local setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # then fill in DATABASE_URL and JWT_SECRET_KEY

alembic revision --autogenerate -m "init tables"
alembic upgrade head

uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs` (FastAPI's auto-generated Swagger UI).

## Folder structure

```
app/
  main.py               -> FastAPI app init, CORS, router registration, scheduler startup
  core/
    config.py           -> environment settings (pydantic-settings)
    security.py         -> password hashing, JWT create/verify
    deps.py             -> get_current_user, require_role() dependency
  db/
    session.py          -> SQLAlchemy engine/session, Base
    models/             -> one file per table
  schemas/               -> Pydantic request/response models
  api/v1/                -> one router file per module (auth, medicines, inventory,
                             suppliers, orders, invoices, alerts, reports)
  services/
    prediction.py        -> Phase 1 rule-based demand prediction
    whatsapp.py           -> single send_whatsapp() wrapper (AiSensy/Gupshup)
    invoice_pdf.py         -> Jinja2 + WeasyPrint GST invoice PDF generation
    scheduler.py            -> APScheduler job definitions (Friday prediction run)
alembic/                     -> DB migrations
```

## Auth endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/auth/login` | Email + password login |
| POST | `/api/v1/auth/signup` | Creates a new business (Client) + its first Client Admin |
| POST | `/api/v1/auth/forgot-password` | Sends a password-reset link (stub logs it to console — see `app/services/email.py`) |
| POST | `/api/v1/auth/reset-password` | Sets a new password using the token from the reset link |
| POST | `/api/v1/auth/refresh` | Issues a new access token from the refresh cookie |
| POST | `/api/v1/auth/logout` | Clears the refresh cookie |

Password reset uses a short-lived (30 min) JWT as the token — no extra database table needed.
`app/services/email.py` currently just prints the reset link to the console; swap in a real
provider (SendGrid, AWS SES, Postmark) there when ready — every caller already goes through
that one function.

## Multi-tenancy

Every tenant-owned table has a `client_id` column. Every query filters by
`current_user.client_id` (pulled from the JWT via `get_current_user`) — this is what
keeps one client's medicines/invoices/suppliers invisible to another client.

## Purchase invoice capture (WhatsApp)

`invoice_attachments` table stores files received either via the WhatsApp webhook
(`POST /api/v1/orders/webhook/whatsapp`) or manual upload
(`POST /api/v1/invoices/attachments`). Staff review a `pending_review` attachment and
link it to a purchase transaction — at that point `invoice_id` gets set and status
becomes `linked`. This keeps the original supplier file attached as proof, with
medicine, supplier, and GST paid all captured on the transaction/invoice itself for
the Profit & Loss report.

## Environment variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | Postgres connection string |
| `JWT_SECRET_KEY` | Long random string — used to sign tokens |
| `JWT_ACCESS_EXPIRE_MINUTES` | Access token lifetime |
| `JWT_REFRESH_EXPIRE_DAYS` | Refresh token (cookie) lifetime |
| `WHATSAPP_PROVIDER` | `aisensy` or `gupshup` |
| `WHATSAPP_API_KEY` | Provider API key |
| `WHATSAPP_API_BASE_URL` | Provider base URL |
| `STORAGE_DIR` | Where invoice PDFs / uploaded attachments are saved |
| `FRONTEND_ORIGIN` | Frontend URL, for CORS |

## Deployment

Dockerfile + docker-compose.yml included — builds a container with WeasyPrint's
system dependencies pre-installed, ready to deploy on the Hetzner VPS covered in the
Requirement Document (same server as the frontend, behind Nginx).

```bash
docker compose up -d --build
```

## Status

Phase 1 scope only — rule-based prediction (no ML yet), single medical-store module.
Super Admin / multi-app endpoints are not built yet, per current priority.
