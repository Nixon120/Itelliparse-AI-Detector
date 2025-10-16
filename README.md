# PowerAI
A Replit-ready full-stack app for detecting AI-generated media with a beautiful UI, auth, webhook signing, and ML stubs.

## Features
- Landing page, Dashboard, Playground, Endpoints, Pricing, Settings
- Email/password auth (session cookie)
- Auth-gated API routes in production (`IP_REQUIRE_AUTH=1`)
- Webhook signing (HMAC-SHA256) and `/webhooks/test` to validate
- ML/DL/NN pseudo-scores + `/v1/metrics` endpoint
- Dockerfile + Procfile

## Env Vars
- `IP_SECRET_KEY` – HMAC secret for webhooks (required if using callbacks)
- `IP_SESSION_SECRET` – session cookie secret
- `IP_STORAGE_DIR` – upload dir (default: `data/uploads`)
- `IP_REQUIRE_AUTH` – set to `1` to require login for API analyze routes

## Run (Replit)
Just press **Run**.

## Run (Local)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
(cd web && npm install && npm run build)
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Sample Webhook Receiver
Run: `uvicorn webhook_receiver:app --host 0.0.0.0 --port 9000`
Then set `options.callback_url` to `http://localhost:9000/webhooks/intelliparse`.
