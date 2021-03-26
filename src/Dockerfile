FROM python:3.7-slim

ENV PYTHONUNBUFFERED 1

RUN apt-get clean \
    && apt-get update -y \
    && apt-get install -y \
        build-essential \
        python3-dev \
        libevent-dev \
        libuv1 \
        libev-dev

# upgrade pip to the latest version.
RUN pip install --upgrade pip

# Set the working directory to /code/
WORKDIR /code/

COPY api/requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY core core/
COPY api/decorators.py api/decorators.py
COPY api/app.py api/app.py

CMD ["gunicorn", "-k", "gevent", "-w", "2", "api.app:app", "-b 0.0.0.0:9001", "-t 300"]
