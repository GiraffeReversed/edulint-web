FROM python:3.8-slim-buster

WORKDIR /app

RUN python3 -m pip install requests toml
COPY utils.py utils.py
COPY setup.py setup.py
ADD https://pypi.org/pypi/edulint/json /tmp/edulint_versions.json
RUN python3 setup.py

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

ENV FLASK_APP app.py
CMD [ "gunicorn", "--bind", "0.0.0.0:5000", "-w", "4", "--worker-class", "sync", "app:app" ]
