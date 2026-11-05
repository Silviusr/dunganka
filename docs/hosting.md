# Hosting configuration

Target: Render native Python, Singapore, Free web service and Free PostgreSQL 17.

Build: `pip install -r requirements.txt && python manage.py collectstatic --noinput`

Start: `python manage.py migrate --noinput && python manage.py seed_demo && python manage.py bootstrap_admin && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 60`

Required secret environment variables: `DATABASE_URL`, `DJANGO_SECRET_KEY`. Runtime flags: `DJANGO_DEBUG=0`, `DJANGO_TRUST_PROXY=1`. Initial staff credentials use the optional `DJANGO_SUPERUSER_*` variables.

The free PostgreSQL created for this demo expires on 2026-12-05. No automatic paid upgrade is configured. Free web service cold starts are expected. Before the database expires, export its demo data or explicitly choose a paid plan or another persistent database.

Public demo data must remain fictional; there are no live payments or fulfilment. Check health, static assets, checkout, staff access and an actual saved order after the deployment completes.
