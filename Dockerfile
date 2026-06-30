FROM python:3.12-slim

ENV TZ=Asia/Tokyo
ENV PYTHONUNBUFFERED=1

ARG REQUIREMENTS=requirements.txt

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
COPY requirements-dev.txt /tmp/requirements-dev.txt

RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir -r /tmp/${REQUIREMENTS}

COPY ./app/ /app/

CMD ["python", "main.py"]
