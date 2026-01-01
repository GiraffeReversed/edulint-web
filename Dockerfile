FROM python:3.14-slim-trixie

WORKDIR /app

ADD https://pypi.org/pypi/edulint/json /tmp/edulint_versions.json
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt && pip freeze

COPY utils.py setup.py pypi_helper.py ./

RUN python3 setup.py

COPY . .

ENV FLASK_APP app.py
ENV PYTHONUNBUFFERED TRUE
CMD [ "gunicorn", \
    "--bind", "0.0.0.0:5000", \
    "--workers", "4", \
    "--worker-class", "gevent", \
    "--max-requests", "500", \
    "--max-requests-jitter", "50", \
    "--access-logfile", "/app/logs/gunicorn_access.log", \
    "--error-logfile", "/app/logs/gunicorn_error.log", \
    "--capture-output", \
    "app:app" ]
