# =========================================================
# ZimFire Monitor — worker image
# Headless polling loop: EUMETSAT MTG + NASA FIRMS VIIRS
# -> risk classification -> GeoJSON/CSV in /app/output
# =========================================================
FROM python:3.12-slim

# Faster, quieter, log-friendly Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencies first (better layer caching). All wheels are
# prebuilt, so no build-essential / GDAL apt packages are needed.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code + the area-of-interest file baked into the image.
# Runtime data (output + sqlite db) lives on volumes, declared below.
COPY config.py main.py healthcheck.py ./
COPY src/aoi.geojson ./src/aoi.geojson

# Create the writable runtime dirs and run as a non-root user.
RUN mkdir -p /app/output /app/src/db \
    && useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

# Lenient healthcheck: container is "healthy" once a monitoring
# cycle has written ranked_fire_alerts.csv recently. Generous
# start period covers the first download/parse cycle.
HEALTHCHECK --interval=2m --timeout=10s --start-period=20m --retries=3 \
    CMD ["python", "healthcheck.py"]

CMD ["python", "main.py"]
