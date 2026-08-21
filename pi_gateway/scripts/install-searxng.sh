#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
    echo "Run this installer with sudo." >&2
    exit 1
fi

source_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
install -d -o root -g root -m 0755 /opt/tars/searxng
install -d -o root -g ember -m 0750 /etc/tars/searxng
install -d -o ember -g ember -m 0750 /var/lib/tars/searxng-cache
install -o root -g root -m 0644 "${source_dir}/searxng/compose.yml" /opt/tars/searxng/compose.yml

if [[ ! -f /etc/tars/searxng/settings.yml ]]; then
    secret="$(openssl rand -hex 32)"
    sed "s/__TARS_SEARXNG_SECRET__/${secret}/" \
        "${source_dir}/searxng/settings.yml.template" \
        >/etc/tars/searxng/settings.yml
    chown root:ember /etc/tars/searxng/settings.yml
    chmod 0640 /etc/tars/searxng/settings.yml
fi

docker compose -p tars -f /opt/tars/searxng/compose.yml pull
docker compose -p tars -f /opt/tars/searxng/compose.yml up -d
echo "Project TARS local SearXNG is bound to 127.0.0.1:8888."
