web: cd farm2market_backend && python ../manage.py migrate && python ../manage.py collectstatic --noinput && gunicorn --pythonpath .. farm2market_backend.wsgi:application --bind 0.0.0.0:$PORT
release: python create_superadmin.py
