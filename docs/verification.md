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
