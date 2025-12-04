web: poetry run gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
release: poetry run python manage.py migrate && poetry run python manage.py initial_setup --skip-superuser || true

