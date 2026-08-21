#!/usr/bin/env bash
set -euo pipefail

env_file="${1:-/etc/tars/tars.env}"
if [[ ! -r ${env_file} ]]; then
    echo "Cannot read ${env_file}; run with sudo on the Pi." >&2
    exit 1
fi

set -a
# shellcheck disable=SC1090
source "${env_file}"
set +a

curl --fail --silent --show-error \
    -H "X-Tars-Token: ${TARS_TOKEN}" \
    http://127.0.0.1:8090/health
printf '\n'
curl --fail --silent --show-error \
    -H "X-Tars-Token: ${TARS_TOKEN}" \
    http://127.0.0.1:8090/capabilities
printf '\n'
