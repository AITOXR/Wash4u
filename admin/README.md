# Wash4You Admin (control plane)

A FastAPI app that lets a non-technical owner edit the whole
[wash4you.in](https://wash4you.in) site — content, products, blog, orders,
customers, settings — without touching code. It runs separately from the
public site (the public site stays a static Python/Jinja2 generator on
GitHub Pages; see the root `README.md` for why).

## How this fits together

```
Public site (content plane)        Admin (control plane, this folder)
──────────────────────────         ───────────────────────────────────
GitHub Pages, static HTML          FastAPI + Postgres, deployed to Railway
content/*.yml, content/posts/*.md  Drafts live in the database
build.py renders it                Publish serialises DB -> content/*.yml/.md,
                                    commits to git, GitHub Actions rebuilds,
                                    Pages redeploys.
```

Nothing here ever gets committed to the site repo except through the
**Publish** button. Orders, leads and customer data (PII) live only in
this app's database — never in git.

## Local setup

```bash
cd admin
python3 -m venv .venv && source .venv/bin/activate    # optional but recommended
pip install -r requirements.txt
cp .env.example .env      # fill in SECRET_KEY (see the comment in .env.example) and ADMIN_INITIAL_PASSWORD
python3 -m app.seed               # creates tables + the one seeded owner account
python3 -m app.seed_content       # (optional, first run only) loads content/ into the DB as published rows
uvicorn app.main:app --reload --port 8811
```

Visit `http://127.0.0.1:8811/admin`, log in with `ADMIN_EMAIL` /
`ADMIN_INITIAL_PASSWORD`, and you'll be forced to set a new password
immediately (by design).

## Running tests

```bash
cd admin
pip install -r requirements.txt   # includes pytest
python3 -m pytest tests/ -v
```

## Deploying (Railway)

1. Create a Railway project, attach a Postgres plugin — it sets
   `DATABASE_URL` automatically.
2. Set the remaining env vars from `.env.example` in Railway's dashboard
   (`SECRET_KEY`, `ADMIN_EMAIL`, `ADMIN_INITIAL_PASSWORD`, `GITHUB_TOKEN`,
   `GITHUB_REPO`, `PUBLIC_SITE_ORIGIN`).
3. Deploy this `admin/` directory (Railway auto-detects the
   `requirements.txt` + `uvicorn` and runs it — add a
   `Procfile`/`railway.toml` with `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   if it doesn't infer the start command).
4. Run `python3 -m app.seed` once (Railway's one-off command / shell) to
   create the schema and seed the owner account.
5. Point `admin.wash4you.in` at the Railway deployment (custom domain, in
   Railway's dashboard) and put it behind HTTPS (Railway does this
   automatically).

### GitHub token for Publish

Publish defaults to a local `git commit` in the checkout at `REPO_PATH`
(fine for local dev). In production, set `GITHUB_TOKEN` (a **fine-grained
PAT**, scoped to `Contents: Read and write` on this one repo only —
Settings → Developer settings → Personal access tokens → Fine-grained) and
`GITHUB_REPO=owner/repo` so Publish commits via the GitHub API instead —
no server-side git checkout or SSH key needed at all. Rotate the token by
generating a new one and updating the env var; nothing else changes.

## Adding a new section type

1. `../schemas/sections/<type>.yml` — the field list (see any existing
   file for the shape: `label`, `description`, `fields: [{key, label,
   type, required?, help?}]`).
2. `../templates/sections/<type>.html` — the Jinja partial that renders it
   on the public site.

That's it — the admin's "+ Add Section" picker and edit form are
generated from the schema automatically (see `app/section_schemas.py` and
`templates/section_form.html`). No Python or route changes needed for a
new section type.

## Known simplifications (flagged, not hidden)

This was built end-to-end and tested (auth, RBAC, section CRUD, live
preview using the real site templates, and the full publish-to-git-commit
pipeline are all genuinely working — see `tests/`), but given the scope of
the full spec, these are real gaps rather than finished features:

- **Repeater fields** (testimonials, FAQ items, steps, etc.) are edited as
  raw JSON in a textarea, not a polished add/remove-row builder. Functional,
  not pretty — see `templates/section_form.html`.
- **No drag-to-reorder** — sections reorder via ↑/↓ buttons (works, including
  on a phone, just not a drag gesture).
- **No 2FA (TOTP) yet** — the `User.totp_secret` / `totp_enabled` columns
  exist but nothing sets or checks them yet.
- **No "shareable preview link"** (signed, expiring token for the client
  to review on their phone before publishing) — `/admin/preview/<id>`
  currently requires being logged into the admin.
- **Email sending is stubbed** — password-reset and order/lead
  notification emails are logged to the console (see `routers/auth.py`),
  not actually sent. Wire up Resend/SMTP once Settings → Integrations
  exists as a real form for those credentials.
- **The `build.py --check` validation in the publish pipeline validates
  content/ as it exists on disk**, not the not-yet-written draft. A
  hardening pass should write drafts to a scratch copy of `content/`,
  validate that, and only copy it over `content/` once it passes — see the
  NOTE comment in `app/publish.py`.
- **Redirects, popups, Turnstile/reCAPTCHA, and the maintenance-mode page
  build.py hook** are modeled in Settings (or not at all, for
  Turnstile) but not fully wired into the public build yet.
- **RBAC is enforced on every route** (tested — see `tests/test_auth.py`),
  but there's no separate `/api/admin/*` JSON surface distinct from the
  HTML admin routes; `require_api_user` exists in `app/deps.py` for when
  one is needed (e.g. an eventual JS-driven inline editor).
