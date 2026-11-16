# Siktio

Siktio tracks where a website shows up in Google for chosen keywords, lists the sites that rank around it, runs an on-page check of one page, and drafts a report with suggestions. A person is meant to read and review every report before anything is done with it.

**Status: prototype.** It runs locally. It is not deployed, has no customers and has no published results. Reports are automatically drafted suggestions; nothing in this repository promises or predicts rankings, traffic or revenue.

Two modes matter, and the app says which one is active on every screen:

| | With credentials | Without credentials (default) |
|---|---|---|
| Rank data | Real, from [DataForSEO](https://docs.dataforseo.com/v3/) | **SAMPLE DATA**: invented fixture values, labelled in the API, the UI and every report |
| Report text | Written by an OpenAI model (`OPENAI_API_KEY`) | A fixed template that states it is a template and not an AI analysis |

Nothing in the default run or in the tests makes a network call to OpenAI, DataForSEO or any other paid service.

## Run it locally

Tested with Python 3.12 and Node 22.

```bash
# 1. Backend
cd seo-backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt

# 2. Web interface (served by the backend once built)
cd ../seo-service-website
npm ci            # .npmrc sets legacy-peer-deps; see "Known quirks"
npm run build

# 3. Start (from seo-backend). The database file is created on first start.
cd ../seo-backend
python -m src.main          # http://127.0.0.1:5000
```

Open http://127.0.0.1:5000, create an account, add a project (website and keywords), press **Run analysis** (sample data, marked as such), then **Generate report** (template report, marked as such).

Front-end development with hot reload: run the backend as above, then `npm run dev` in `seo-service-website` (it proxies `/api` to port 5000; set `VITE_API_TARGET` to change that).

Handy commands, from `seo-backend`:

```bash
python -m src.manage init-db                   # create/upgrade the database explicitly (the app also does this at start)
python -m src.manage create-user you@example.com --plan starter   # asks for the password
pytest                                          # backend tests, no network
```

## Configure

All settings are environment variables; [`.env.example`](.env.example) lists every one with its purpose and default. The important ones:

| Variable | What it does |
|---|---|
| `APP_ENV` | `development` (default) or `production`. In production the app **refuses to start** without a strong `SECRET_KEY` and turns on secure cookies. |
| `SECRET_KEY` | Signs session cookies. Required in production (32+ random characters). In development a random per-process key is used if unset. There is no built-in key. |
| `DATABASE_URL` | Empty = SQLite file in `seo-backend/instance/`, created by code. |
| `CORS_ORIGINS` | Explicit list of other origins allowed to call the API with cookies. Empty (default) = none. `*` is refused. |
| `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD` | Turn on real rank data. Both or neither. |
| `OPENAI_API_KEY`, `OPENAI_MODEL` | Turn on AI-written report text. The model name is configuration; pick one your account can use. |
| `RANK_PROVIDER`, `REPORT_GENERATOR` | Force `sample` / `template`, or require `dataforseo` / `openai`. Default `auto`. |
| `ALLOW_REGISTRATION` | `0` closes sign-up (use `manage create-user`). Worth doing once real credentials are set, since every analysis costs money. |
| `MAX_ANALYSES_PER_USER_PER_DAY` | Cost guard for real data. |

With credentials set, `GET /api/health` shows `"rank_provider": "dataforseo"` and `"report_generator": "openai"`. It never shows the keys.

## Docker

`Dockerfile` (multi-stage: builds the web interface, then runs the Flask app under gunicorn) and `docker-compose.yml` are included:

```bash
cp .env.example .env     # set SECRET_KEY at least
docker compose up --build   # http://127.0.0.1:8000, data in the siktio-data volume
```

The image runs as a non-root user, listens on port 8000, has a health check on `/api/health`, and keeps SQLite in `/data`. It uses one gunicorn worker with threads, because the login throttle is in memory. **The Dockerfile and compose file have not been built or run** (see below). Put a TLS-terminating reverse proxy in front and set `TRUST_PROXY_HEADERS=1` for anything public.

## How it works

```
React UI  ->  Flask API  ->  RankProvider  ->  DataForSEOClient (real)  |  SampleProvider (fixture)
                         ->  analysis.py  (rank for your domain, competitors, technical audit)
                         ->  reports/     (OpenAI via one function, else template)  ->  SQLite
```

- **Provider interface** (`src/providers/base.py`): `get_serp`, `get_keyword_metrics`, `audit_page`, plus an `is_sample` flag that flows into every analysis, dashboard and report.
- **DataForSEO client** (`src/providers/dataforseo.py`), HTTP Basic auth, "Live" endpoints:
  - `POST /v3/serp/google/organic/live/advanced` for organic results per keyword (position = `rank_group` among `organic` items),
  - `POST /v3/keywords_data/google_ads/search_volume/live` for monthly search volume,
  - `POST /v3/dataforseo_labs/google/bulk_keyword_difficulty/live` for keyword difficulty,
  - `POST /v3/on_page/instant_pages` for the technical check of one page.

  Rate limits (HTTP 429, status 40202, 40209) and transient errors (40101, 40103, 50000, 50301, 50303, 50401, 50402, HTTP 5xx, network errors) are retried with exponential backoff and `Retry-After`. Auth (401/40100), payment (402/40200/40203/40210) and request errors are not retried and become clean API errors. Credentials are not logged or put in messages.
- **Competitors** are derived from the SERP data you already paid for: domains other than your own in the top 10 of your keywords, ordered by how many keywords they appear for, then by average position. No extra endpoint.
- **Sample provider** (`src/providers/sample.py`): deterministic fixture values; competitor domains use the reserved `.example` TLD; technical findings are titled "Sample finding".
- **Reports** (`src/reports/`): sections are summary, ranking analysis, competitor analysis, content suggestions, technical recommendations, action plan. The single OpenAI call is `call_openai` in `src/reports/openai_client.py`; tests replace it. If OpenAI is configured but fails or returns unusable output, the report falls back to the template and says why (`fallback_reason`). The disclaimer, the "template vs AI" note and the sample-data flag are attached by code, not by the model.
- **API** (JSON, cookie session; every state-changing request must send `X-Requested-With: siktio-web`):
  `POST /api/auth/register|login|logout`, `GET /api/auth/me`, `GET|POST /api/projects`, `GET|PATCH|DELETE /api/projects/<id>`, `POST /api/projects/<id>/analyze`, `GET /api/projects/<id>/dashboard`, `GET /api/projects/<id>/analyses/latest`, `GET|POST /api/projects/<id>/reports`, `GET|DELETE /api/reports/<id>`, `POST /api/reports/<id>/review`, `GET /api/health`.

## What works / what does not

**Verified here** (backend tests: 141 passing, no network; front end: `npm run build` succeeds; the app was also run and clicked through in a browser):

- Create account, sign in, create a project, run an analysis, generate a report, mark it reviewed: end to end with sample data, labelled SAMPLE DATA in the API payloads, the dashboard and the report page.
- Template reports, with the review disclaimer and no promises, and the OpenAI path with the model call mocked (including fallback to the template on errors or malformed output).
- DataForSEO client request construction, Basic auth, response mapping, error classification, retries and backoff, against a fake HTTP layer.
- Passwords stored as salted hashes (Werkzeug scrypt); login throttling; CSRF header requirement; per-user isolation (another user gets 404 on every project, analysis and report route); CORS closed by default; input validation; no secrets in responses; production mode fails closed without `SECRET_KEY`; the database is created by code and is not in the repository.
- The app starts under gunicorn in production mode from `requirements.txt` alone.

**Not verified, or not working:**

- **DataForSEO against the real API.** No credentials were available. Request and response shapes come from the official documentation; the tests use hand-written fixtures in those shapes. Unconfirmed: that the `location_name`/`language_code` values you enter are accepted, that every endpoint is enabled on your account, the per-call cost (`SERP_DEPTH` above 10 can cost more), and the details of the `on_page/instant_pages` response for unusual pages.
- **OpenAI against the real API.** Written against the Python SDK's Chat Completions interface with a mocked client. The default `OPENAI_MODEL` is a guess you should change. The prompt tells the model not to promise results and to treat data as data, but nothing can enforce that for model-written text, which is why every report needs human review.
- The Docker image and compose file were not built or run. Only SQLite is tested.
- Analyses run inside the web request, one keyword after another. A long keyword list against the real API takes a while (the gunicorn timeout is 300 s); there is no background queue.
- Technical check covers the single page you enter, not the site. The competitor list shows who ranks, not why. A "not found" position means not found in the first `SERP_DEPTH` results.
- Report language is English only; the UI is English only.
- Not built: payments or billing (the plan only limits keywords per project; the prices on the Plans page are drafts and nothing can be bought), email, scheduled or recurring analyses, trend history beyond "compared with the previous check", PDF export (the earlier prototype had a PDF generator; it was dropped).
- No password reset or email verification.
- Rate limiting for logins is per process and in memory.

## Tests and build

```bash
cd seo-backend && pytest            # 141 tests, deterministic, no network
cd seo-service-website && npm run build && npm run lint
```

The tests build the app with `create_app({...})`, which reads only the mapping it is given, so keys in your shell cannot leak in. DataForSEO is tested through a fake `requests` adapter; OpenAI through an injected callable and a monkeypatched SDK client.

## Known quirks

- `npm ci` needs `legacy-peer-deps` (set in `seo-service-website/.npmrc`): `react-day-picker@8` declares a peer of `date-fns` up to 3 while the project uses 4. The repository also holds a `pnpm-lock.yaml`; the Dockerfile and this README use `package-lock.json`.
- Earlier history of this repository contains a hard-coded Flask secret key and a committed `node_modules`. The key is no longer used anywhere, so there is nothing to rotate; history was not rewritten.
- The old `clean_repo.sh` (which force-pushed to `main`) and `deploy.sh` (hard-coded home-directory paths, `pkill`) were removed.
