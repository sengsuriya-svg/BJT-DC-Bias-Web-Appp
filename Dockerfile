FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Docker builds run as root, so the OS-level ngspice package can be installed
# here. This avoids the permission restriction of Render's free Native runtime.
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ngspice \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 7860
CMD gunicorn --bind 0.0.0.0:${PORT:-7860} --workers 1 --timeout 120 app:app
