FROM python:3.8-slim

WORKDIR /app

RUN apt-get update && apt-get install -y openssl curl
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
COPY poetry.lock pyproject.toml poetry.toml /app/
RUN cd /app && /root/.poetry/bin/poetry install --no-dev

COPY . /app/

ENTRYPOINT [ "/root/.poetry/bin/poetry", "run", "python", "runserver.py" ]
