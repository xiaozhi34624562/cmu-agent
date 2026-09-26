FROM python:3.10-slim-bookworm
RUN pip install --progress-bar off --no-cache-dir -U pip==21.0.1
COPY requirements.txt /tmp/requirements.txt
RUN pip install --progress-bar off --no-cache-dir -r /tmp/requirements.txt
WORKDIR /home/aicrowd
COPY . .
