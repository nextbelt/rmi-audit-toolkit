# ── Production backend image ───────────────────────────────────────────────
# Built FROM the official Playwright Python image, which ships headless
# Chromium plus every system library it needs at the correct FHS paths. This
# is what makes the premium HTML→PDF report renderer work reliably in prod.
#
# Why not Nixpacks: Nixpacks installs Chromium fine, but its Nix-based runtime
# does not expose the browser's shared libraries (libstdc++.so.6, etc.) on the
# loader path, so Chromium fails to launch. The app still has a ReportLab
# fallback, but this image makes the premium renderer the actual default.
#
# Pinned to the same Playwright version as requirements.txt (1.47.0); the base
# tag's Chromium build is guaranteed compatible. jammy => Python 3.10 (the app
# uses no 3.11-only features).

FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy

WORKDIR /app

# python-magic needs libmagic1 (not present in the base image).
RUN apt-get update \
    && apt-get install -y --no-install-recommends libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first so this layer is cached unless requirements change.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Ensure the Chromium build matching the pinned Playwright version is present.
# It is already in the base image, so this is a fast no-op safeguard against
# any future version drift between the base tag and the pip pin.
RUN python -m playwright install chromium

# App source (see .dockerignore for what is intentionally excluded).
COPY . .

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# Railway routes/healthchecks the service's target port. Unlike the Nixpacks
# provider, a Dockerfile build does NOT receive an auto-generated PORT, so we
# pin it here (and the start command falls back to 8080 if PORT is unset).
EXPOSE 8080

# serve.py runs DB migrations in a background thread (self-healing + retrying
# while Railway's private network initializes) and binds a dual-stack (IPv6 +
# IPv4) socket so the IPv6 private-network healthcheck can reach the app.
# Railway's deploy.startCommand overrides this CMD in production, but it keeps
# the image runnable standalone.
CMD ["python", "serve.py"]
