FROM python:3.8-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY utils.py utils.py
COPY setup.py setup.py
COPY pypi_helper.py pypi_helper.py

ADD https://pypi.org/pypi/edulint/json /tmp/edulint_versions.json
RUN python3 setup.py

COPY . .

ENV FLASK_APP app.py
ENV PYTHONUNBUFFERED TRUE
CMD [ "gunicorn", \
    "--bind", "0.0.0.0:5000", \
    "--workers", "4", \
    "--worker-class", "sync", \
    "--access-logfile", "/app/logs/gunicorn_access.log", \
    "--error-logfile", "/app/logs/gunicorn_error.log", \
    "--capture-output", \
    "app:app" ]
