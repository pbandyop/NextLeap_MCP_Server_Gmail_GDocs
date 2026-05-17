# Railway Deployment Plan — saksham-mcp-server

Deploy the FastAPI-based Google Docs + Gmail MCP server to [Railway](https://railway.app).

This service exposes HTTP endpoints (`/tools`, `/append_to_doc`, `/create_email_draft`). Railway runs it with **Nixpacks** using `railway.toml`, `requirements.txt`, and `.python-version` (Python 3.11.9).

---

## Architecture

```
Client (curl / AI workflow)
        │ HTTPS
        ▼
Railway (uvicorn → server.py)
        │
        ├── GOOGLE_CREDENTIALS_JSON → credentials.json (on disk at startup)
        ├── GOOGLE_TOKEN_JSON       → auth.py (in-memory; no browser OAuth)
        └── Google Docs + Gmail APIs
```

| File / setting | Purpose |
|----------------|---------|
| `railway.toml` | Start command, health check on `/`, restart policy |
| `.python-version` | Pins Python `3.11.9` for Nixpacks |
| `server.py` | Materializes `credentials.json` from env; auto-approves on Railway |
| `auth.py` | Loads `GOOGLE_TOKEN_JSON`; disables interactive OAuth when `RAILWAY_ENVIRONMENT` is set |

`PORT` and `RAILWAY_ENVIRONMENT` are injected automatically by Railway.

---

## Phase 1 — Google Cloud (one-time)

1. Open [Google Cloud Console](https://console.cloud.google.com/) and create or select a project.
2. **Enable APIs:** Google Docs API, Gmail API.
3. **OAuth consent screen:** configure (External is fine for personal use). Add your Google account as a **test user** while the app is in Testing mode.
4. **Credentials → Create OAuth client ID → Desktop app** → download `credentials.json`.
5. Place `credentials.json` in the project root (never commit it).

---

## Phase 2 — Local OAuth (required before deploy)

Railway cannot open a browser for OAuth. Generate `token.json` on your machine first.

**macOS / Linux:**

```bash
python3 auth.py
```

**Windows (PowerShell):**

```powershell
python auth.py
```

Or run `auth.bat` from the project folder.

You should see `Done. token.json has been saved.` Both `credentials.json` and `token.json` are listed in `.gitignore` — use environment variables on Railway, not git.

---

## Phase 3 — Push to GitHub

1. Create a GitHub repository for this project.
2. Push the `main` branch (include `railway.toml`, `requirements.txt`, `.python-version`, application code).
3. Confirm `credentials.json` and `token.json` are **not** in the repo.

---

## Phase 4 — Create the Railway service

### Option A — Dashboard (recommended)

1. [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo** → select this repository.
2. Railway builds with Nixpacks (`requirements.txt` + `.python-version`).
3. Open the service → **Variables** → add the three variables in [Phase 5](#phase-5--environment-variables).
4. **Settings → Networking → Generate Domain** → copy your `*.up.railway.app` URL.
5. Wait for the deploy to finish (health check: `GET /`).

### Option B — CLI

**macOS / Linux:**

```bash
npm install -g @railway/cli
railway login
railway init
railway link
railway variables set AUTO_APPROVE=true
railway variables set GOOGLE_CREDENTIALS_JSON="$(cat credentials.json)"
railway variables set GOOGLE_TOKEN_JSON="$(cat token.json)"
railway up
```

**Windows (PowerShell):**

```powershell
npm install -g @railway/cli
railway login
railway init
railway link
railway variables set AUTO_APPROVE=true
railway variables set GOOGLE_CREDENTIALS_JSON="$(Get-Content credentials.json -Raw)"
railway variables set GOOGLE_TOKEN_JSON="$(Get-Content token.json -Raw)"
railway up
```

Generate a public URL in the dashboard (**Networking → Generate Domain**) if you use the CLI.

---

## Phase 5 — Environment variables

| Variable | Value | Required |
|----------|--------|----------|
| `AUTO_APPROVE` | `true` | Yes |
| `GOOGLE_CREDENTIALS_JSON` | Full contents of `credentials.json` | Yes |
| `GOOGLE_TOKEN_JSON` | Full contents of `token.json` | Yes |
| `PYTHON_VERSION` | `3.11.9` | No (`.python-version` is in the repo) |

**Dashboard tips:**

- Paste the **entire** JSON object for each secret (starts with `{`, ends with `}`).
- Do not wrap the value in extra quotes unless Railway’s UI adds them for you.
- After changing secrets, trigger a **Redeploy**.

See `.env.example` for a local reference (copy to `.env` only for local dev; Railway uses the Variables tab).

---

## Phase 6 — Post-deploy verification

Replace `<your-service>` with your Railway domain.

**macOS / Linux:**

```bash
APP=https://<your-service>.up.railway.app

curl "$APP/"
curl "$APP/tools"

curl -X POST "$APP/append_to_doc" \
  -H "Content-Type: application/json" \
  -d '{"doc_id":"<google-doc-id>","content":"hello from railway"}'

curl -X POST "$APP/create_email_draft" \
  -H "Content-Type: application/json" \
  -d '{"to":"you@example.com","subject":"test","body":"hi"}'
```

**Windows (PowerShell):**

```powershell
$APP = "https://<your-service>.up.railway.app"

Invoke-RestMethod "$APP/"
Invoke-RestMethod "$APP/tools"

Invoke-RestMethod -Method Post -Uri "$APP/append_to_doc" `
  -ContentType "application/json" `
  -Body '{"doc_id":"<google-doc-id>","content":"hello from railway"}'

Invoke-RestMethod -Method Post -Uri "$APP/create_email_draft" `
  -ContentType "application/json" `
  -Body '{"to":"you@example.com","subject":"test","body":"hi"}'
```

**Health check response** (`GET /`):

```json
{
  "message": "Google MCP Server is running 🚀",
  "deployed": true,
  "credentials_ready": true,
  "token_configured": true
}
```

If `credentials_ready` or `token_configured` is `false`, fix the corresponding Railway variable and redeploy.

**Logs:**

```bash
railway logs
```

Watch for `credentials.json created from GOOGLE_CREDENTIALS_JSON` and API errors (403 = doc not shared with the OAuth account).

---

## Phase 7 — Connect your AI / MCP client

Point your integration at the public Railway base URL:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tools` | GET | List available tools |
| `/append_to_doc` | POST | Append text to a Google Doc |
| `/create_email_draft` | POST | Create a Gmail draft (does not send) |

The Google Doc must be editable by the Google account used during local OAuth.

---

## Token refresh and redeploys

Railway containers are **ephemeral** — the filesystem resets on each deploy. In production:

- `GOOGLE_TOKEN_JSON` is the source of truth (not a file on disk).
- `auth.py` refreshes expired access tokens in memory when a refresh token is present.
- Refreshed tokens are **not** written back to Railway variables automatically.

**When to update `GOOGLE_TOKEN_JSON`:**

- Token revoked in Google Account settings
- OAuth client regenerated
- Errors: `Missing GOOGLE_TOKEN_JSON` or invalid token

**Fix:** run `python auth.py` locally, then update `GOOGLE_TOKEN_JSON` in Railway and redeploy.

**Optional (advanced):** attach a [Railway Volume](https://docs.railway.app/guides/volumes) and persist `token.json` on a mount so refreshes survive redeploys (requires a small `auth.py` change to write to the volume path when deployed).

---

## Security checklist

- Never commit `credentials.json`, `token.json`, or `.env`.
- Restrict who can access the Railway project and variables.
- `AUTO_APPROVE=true` skips human approval — only use on a URL you trust.
- Keep OAuth consent screen test users minimal while in Testing mode.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|----------------|-----|
| Build fails on Python | Wrong runtime | Confirm `.python-version` is `3.11.9` or set `PYTHON_VERSION` |
| Health check fails | App not listening on `$PORT` | `railway.toml` already binds uvicorn to `$PORT` |
| `credentials_ready: false` | Missing / empty `GOOGLE_CREDENTIALS_JSON` | Paste full `credentials.json` JSON |
| `token_configured: false` | Missing `GOOGLE_TOKEN_JSON` | Paste full `token.json` JSON |
| `GOOGLE_TOKEN_JSON is not valid JSON` | Truncated or quoted incorrectly | Re-paste entire file |
| Google 403 on Docs | Doc not shared | Share doc with the OAuth Google account |
| Gmail draft fails | API / scope | Enable Gmail API; re-run OAuth if scopes changed |

---

## Repository deploy assets (summary)

| Asset | Status |
|-------|--------|
| `railway.toml` | Start command, `/` health check |
| `.python-version` | `3.11.9` |
| `auth.py` | Cloud detection via `RAILWAY_ENVIRONMENT` |
| `server.py` | Env-based credentials + deploy health fields |
| `.env.example` | Local variable reference |
| `render.yaml` | Legacy Render config (ignored by Railway) |

---

## Quick checklist

- [ ] Google Docs + Gmail APIs enabled
- [ ] `credentials.json` and `token.json` generated locally (`python auth.py`)
- [ ] Code pushed to GitHub (no secrets in repo)
- [ ] Railway project linked to repo
- [ ] `AUTO_APPROVE`, `GOOGLE_CREDENTIALS_JSON`, `GOOGLE_TOKEN_JSON` set
- [ ] Public domain generated
- [ ] `GET /` shows `credentials_ready` and `token_configured` as `true`
- [ ] Test `POST /append_to_doc` and `POST /create_email_draft`
