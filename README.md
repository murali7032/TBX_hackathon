# TBX Insight

Grounded finance assistant for **TBX Finance** (BVP Tech Catalyst Hackathon).

Ask plain-language questions about banks, accounts, and transactions. Every number comes from PostgreSQL via read-only SQL tools — the model explains results; it does not invent them.

**Stack:** React (Vite) · FastAPI · PostgreSQL · Google Gemini (Flash / Flash-Lite)

---

## Architecture

```text
┌──────────────┐     HTTP      ┌─────────────────┐     tools      ┌──────────────────┐
│  TBX Insight │ ───────────► │  FastAPI API     │ ────────────► │  Gemini agent    │
│  React UI    │ ◄─────────── │  /chat · /api    │ ◄──────────── │  tool-calling    │
│  Dashboard   │   JSON +     │  /export         │   evidence    │  + session memory│
└──────────────┘   evidence   └────────┬────────┘               └────────┬─────────┘
                                       │                                  │
                                       │ SQLAlchemy                       │ read-only
                                       ▼                                  │ SELECT/WITH
                              ┌─────────────────┐                         │
                              │  PostgreSQL 18  │ ◄───────────────────────┘
                              │  finance DB     │
                              │  bank           │
                              │  account        │
                              │  "transaction"  │
                              └─────────────────┘
```

### Request path

1. **Ask** — User sends a natural-language question (`optimize_for` optional).
2. **Clarify** — Ambiguous bank / last-4 → account choice chips.
3. **Plan** — Gemini picks tools using the schema guide.
4. **Query** — Read-only SQL against Postgres.
5. **Evidence** — Result rows + SQL kept for the UI.
6. **Answer** — Plain-language reply narrated only from those rows.

### Agent tools

| Tool | Purpose |
|------|---------|
| `read_database_guide` | Loads [`database/LLM_TOOL_GUIDE.md`](database/LLM_TOOL_GUIDE.md) |
| `list_tables` | Column metadata from `information_schema` |
| `run_sql_query` | Read-only `SELECT` / `WITH` |
| `find_accounts` | Account search for clarification chips |
| `analyze_debit_trends` | MoM spend + anomaly signals |

### Data model

```text
bank (1) ──< account (many) ──< "transaction" (many)
```

Seed size: **10 banks · 10 accounts · 10 transactions**.

---

## Setup instructions

### Prerequisites

- Python **3.11+**
- Node.js **18+** and npm
- Network access to the Postgres host (or your own Postgres with the seed loaded)
- A **Google Gemini API key**

### 1. Clone

```powershell
git clone https://github.com/murali7032/TBX_hackathon.git
cd TBX_hackathon
```

### 2. Database

Demo connection (remote EC2 Postgres):

| Setting | Value |
|---------|--------|
| Host | `50.17.70.100` |
| Port | `5432` |
| Database | `finance` |
| User | `finance_user` |
| Password | `finance_password` |

Schema and seed notes: [`database/dataset`](database/dataset) · tool guide: [`database/LLM_TOOL_GUIDE.md`](database/LLM_TOOL_GUIDE.md)

Optional local Postgres via Docker:

```powershell
cd database
docker compose up -d
```

Update `DATABASE_URL` in `backend/.env` if you use local Docker instead of the remote host.

### 3. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg2://finance_user:finance_password@50.17.70.100:5432/finance
GEMINI_API_KEY=your_key_here
GEMINI_OPTIMIZE_FOR=balanced
DATABASE_GUIDE_PATH=../database/LLM_TOOL_GUIDE.md
```

| Variable | Purpose |
|----------|---------|
| `GEMINI_API_KEY` | Required for `/chat` |
| `GEMINI_OPTIMIZE_FOR` | `cost` \| `balanced` \| `intelligence` |
| `GEMINI_MODEL` | Optional fixed model id (overrides mapping) |
| `DATABASE_URL` | SQLAlchemy Postgres URL |
| `DATABASE_GUIDE_PATH` | Path to the LLM schema guide |

Model mapping:

| `optimize_for` | Model |
|----------------|--------|
| `cost` | `gemini-3.5-flash-lite` |
| `balanced` | `gemini-3.5-flash` |
| `intelligence` | `gemini-3.5-flash` |

Start the API:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 4. Frontend

```powershell
cd frontend
npm install
copy .env.example .env
```

Ensure `frontend/.env` points at the API:

```env
VITE_API_URL=http://127.0.0.1:8000
```

```powershell
npm run dev
```

Open the URL Vite prints (usually [http://127.0.0.1:5173](http://127.0.0.1:5173)).

### 5. Quick smoke test

1. Open **Dashboard** — metrics and spend charts load from `/api/*`.
2. Open **TBX Insight** chat — ask: `What's the balance for HDFC accounts?`
3. Expand **View evidence & SQL** — confirm rows + query.
4. Try: `Find transaction with ref HDFCH01078329532`

---

## API map

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/chat` | NL Q&A via Gemini + tools |
| `POST` | `/chat/feedback` | Thumbs up/down (down regenerates SQL) |
| `GET` / `DELETE` | `/chat/{session_id}` | History / reset |
| `GET` | `/health` | DB connectivity + row counts |
| `GET` | `/api/banks` | Banks |
| `GET` | `/api/accounts` | Accounts |
| `GET` | `/api/transactions` | Transactions |
| `POST` | `/api/sql` | Read-only SQL |
| `POST` / `GET` | `/export/csv` · `/export/xlsx` | Evidence export |

Example chat body:

```json
{
  "message": "What's the balance for HDFC accounts?",
  "session_id": null,
  "optimize_for": "balanced"
}
```

---

## Product surfaces

- **Dashboard** — debit/credit totals, spend by bank, top payees
- **TBX Insight** — grounded chat with clarification chips, MoM/anomaly callouts, collapsible evidence, CSV/Excel export
- **Banks / Accounts / Transactions** — browse ledger tables

---

## Repo layout

```text
TBX_hackathon/
├── backend/          # FastAPI + Gemini agent
├── frontend/         # React (Vite) UI
├── database/         # Schema notes, seed, LLM tool guide, docker-compose
├── docs/             # Presentation deck + generator
└── README.md
```

