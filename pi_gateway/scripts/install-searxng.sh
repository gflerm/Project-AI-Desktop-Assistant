#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
    echo "Run this installer with sudo." >&2
    exit 1
fi

source_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
install -d -o root -g root -m 0755 /opt/james/searxng
install -d -o root -g ember -m 0750 /etc/james/searxng
install -d -o ember -g ember -m 0750 /var/lib/james/searxng-cache
install -o root -g root -m 0644 "${source_dir}/searxng/compose.yml" /opt/james/searxng/compose.yml

if [[ ! -f /etc/james/searxng/settings.yml ]]; then
    secret="$(openssl rand -hex 32)"
    sed "s/__JAMES_SEARXNG_SECRET__/${secret}/" \
        "${source_dir}/searxng/settings.yml.template" \
        >/etc/james/searxng/settings.yml
    chown root:ember /etc/james/searxng/settings.yml
    chmod 0640 /etc/james/searxng/settings.yml
fi

docker compose -p james -f /opt/james/searxng/compose.yml pull
docker compose -p james -f /opt/james/searxng/compose.yml up -d
echo "Project James local SearXNG is bound to 127.0.0.1:8888."
