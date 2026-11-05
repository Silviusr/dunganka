# Verification record

- Python 3.13.0, Django 5.2.19.
- 18 integration tests passed after independent runtime review.
- Reviewer found one Important issue: deleted menu items trapped a session cart. Added a failing regression, then removed missing items with a visible notice on the cart page; full suite passed.
- Browser checked at 1440×1000 and 390×844. Catalog, cart and checkout rendered without horizontal overflow. All hero/menu images loaded.
- Browser completed one fictional preorder, displayed its number, food subtotal, dispatch date and unconfirmed delivery status.
- Screenshots in docs/screenshots contain only generated artwork and fictional data.
- Staff login and delivery/status editing verified in the browser as well as integration tests: 12,000 KRW food plus 4,000 KRW delivery displayed as 16,000 KRW on the originating receipt. Docker build is not claimed as tested here.
- A public deployment and GitHub Actions run require publication and are not part of these local results.

- Full suite: `python manage.py test` from repository directory: 18 tests, OK.
- `check`, `makemigrations --check --dry-run` and `collectstatic --noinput` succeeded.
- `check --deploy --fail-level WARNING` with DEBUG=0, an ephemeral strong key and an example HTTPS origin succeeded without warnings.
- Gunicorn started with one worker/two threads; HTTP smoke checks for catalog and static CSS both returned 200.

## Hosted verification — 2026-11-05

- Public demo: https://dunganka.onrender.com/
- Live runtime commit: `3b3c920bb42d5e4b711fdbaa2efea53fcb3f3b44`.
- Render deployment `dep-dbm3bmg8v5cc73df9ul0` reached `live`.
- 27 tests passed locally and in [GitHub Actions](https://github.com/Silviusr/dunganka/actions/runs/41989975989), including production catalog rendering against collected, hashed static assets.
- HTTPS health endpoint returned 200 with `status=ok`, HSTS and no-store. Homepage returned 200; browser confirmed every displayed image loaded.
- Browser completed a fictional preorder over HTTPS. Staff login succeeded; the order appeared in the PostgreSQL-backed admin.
- Staff entered 4,000 KRW delivery and confirmed the order; the original browser receipt displayed 12,000 KRW food plus delivery = 16,000 KRW.
- Fetching that receipt without its session returned 404.
- Render Free PostgreSQL 17 is in Singapore and expires 2026-12-05. Render Free web service uses native Python/Gunicorn and `/healthz/` readiness. No paid service created.
- Because the service uses a public Git repository URL, releases are manual; the service auto-deploy flag is Off.
- Hosting credentials are outside the repository; no secret, database file or real customer data was published.
