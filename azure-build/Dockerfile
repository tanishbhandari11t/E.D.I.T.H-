# Slim Jimmy image: dashboard + agent + prebuilt Ink TUI for /chat.
# Node binary comes from the official image (no NodeSource — avoids ACR log unicode issues).
FROM node:22-bookworm-slim AS nodebin

FROM python:3.13-slim-bookworm
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    HERMES_HOME=/opt/data HOME=/opt/data \
    PATH="/opt/jimmy/.venv/bin:/usr/local/bin:$PATH" \
    HERMES_DASHBOARD=1 HERMES_DASHBOARD_HOST=0.0.0.0 HERMES_DASHBOARD_PORT=9119 \
    JIMMY_SEED_PROFILES=1 JIMMY_DISABLE_LOGIN_RATE_LIMIT=1
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl git ripgrep \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -u 10000 -m -d /opt/data jimmy
# Copy node + npm from official Node image (runs hermes_cli/tui_dist/entry.js).
COPY --from=nodebin /usr/local/bin/node /usr/local/bin/node
COPY --from=nodebin /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -sf /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
 && node --version
WORKDIR /opt/jimmy
COPY . .
RUN test -f /opt/jimmy/hermes_cli/tui_dist/entry.js
RUN python -m venv /opt/jimmy/.venv \
 && /opt/jimmy/.venv/bin/pip install -U pip wheel \
 && /opt/jimmy/.venv/bin/pip install --no-cache-dir -e . \
 && chown -R jimmy:jimmy /opt/jimmy /opt/data
USER jimmy
WORKDIR /opt/data
EXPOSE 9119
CMD ["sh","-c","python -m hermes_cli.jimmy_seed_profiles || true; exec hermes dashboard --host 0.0.0.0 --port 9119 --no-open"]
