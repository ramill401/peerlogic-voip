web: poetry run python manage.py migrate && poetry run python manage.py initial_setup && poetry run python manage.py collectstatic --noinput && poetry run gunicorn config.wsgi:application --bind 0.0.0.0:$PORT

