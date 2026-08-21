#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
    echo "Run this installer with sudo." >&2
    exit 1
fi

source_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
test -x /opt/ember/venv/bin/uvicorn
getent passwd ember >/dev/null

install -d -o root -g root -m 0755 /opt/james/gateway
install -d -o ember -g ember -m 0755 /opt/james/models/piper
install -d -o ember -g ember -m 0750 /var/lib/james
install -d -o root -g ember -m 0750 /etc/james
cp -a "${source_dir}/james_gateway" /opt/james/gateway/
install -o root -g root -m 0644 "${source_dir}/requirements.txt" /opt/james/gateway/requirements.txt

if [[ ! -f /etc/james/james.env ]]; then
    token="$(openssl rand -hex 32)"
    umask 0027
    {
        printf 'JAMES_TOKEN=%s\n' "${token}"
        printf 'JAMES_WHISPER_URL=http://127.0.0.1:8080\n'
        printf 'JAMES_PIPER_URL=http://127.0.0.1:5001\n'
        printf 'JAMES_OLLAMA_URL=http://127.0.0.1:11434\n'
        printf 'JAMES_LLM_PROVIDER=auto\n'
        printf 'JAMES_GEMINI_MODEL=gemini-3.5-flash-lite\n'
        printf 'JAMES_GEMINI_GOOGLE_SEARCH=true\n'
        printf 'JAMES_LLM_FALLBACK_TO_OLLAMA=true\n'
        printf 'JAMES_OLLAMA_MODEL=qwen3:1.7b\n'
        printf 'JAMES_OLLAMA_THINK=false\n'
        printf 'JAMES_WEATHER_LAT=-33.9249\n'
        printf 'JAMES_WEATHER_LON=18.4241\n'
        printf 'JAMES_WEATHER_PLACE=Cape Town, Western Cape, South Africa\n'
        printf 'JAMES_TTS_LENGTH_SCALE=0.94\n'
        printf 'JAMES_TTS_NOISE_SCALE=0.76\n'
        printf 'JAMES_TTS_NOISE_W_SCALE=0.90\n'
        printf 'JAMES_TELEMETRY_ENABLED=true\n'
        printf 'JAMES_TELEMETRY_INCLUDE_TEXT=false\n'
        printf 'JAMES_TELEMETRY_PATH=/var/lib/james/telemetry.jsonl\n'
        printf 'JAMES_TELEMETRY_MAX_BYTES=10485760\n'
        printf 'JAMES_PERSONALITY_PATH=/var/lib/james/personality.json\n'
        printf 'JAMES_SPEECH_ADAPTATION_PATH=/var/lib/james/speech-adaptation.json\n'
        printf 'JAMES_LOCAL_LEARNING_PATH=/var/lib/james/local-lessons.json\n'
        printf 'JAMES_PERSISTENT_MEMORY_PATH=/var/lib/james/persistent-memory.json\n'
        printf 'JAMES_SEARXNG_URL=http://127.0.0.1:8888\n'
        printf 'JAMES_SESSION_MAX_TURNS=3\n'
        printf 'JAMES_MAX_UTTERANCE_BYTES=1048576\n'
    } >/etc/james/james.env
    chown root:ember /etc/james/james.env
    chmod 0640 /etc/james/james.env
fi

ensure_setting() {
    local key="$1"
    local value="$2"
    if ! grep -q "^${key}=" /etc/james/james.env; then
        printf '%s=%s\n' "${key}" "${value}" >>/etc/james/james.env
    fi
}

ensure_setting JAMES_GEMINI_GOOGLE_SEARCH true
ensure_setting JAMES_TTS_LENGTH_SCALE 0.94
ensure_setting JAMES_TTS_NOISE_SCALE 0.76
ensure_setting JAMES_TTS_NOISE_W_SCALE 0.90
ensure_setting JAMES_TELEMETRY_ENABLED true
ensure_setting JAMES_TELEMETRY_INCLUDE_TEXT false
ensure_setting JAMES_TELEMETRY_PATH /var/lib/james/telemetry.jsonl
ensure_setting JAMES_TELEMETRY_MAX_BYTES 10485760
ensure_setting JAMES_PERSONALITY_PATH /var/lib/james/personality.json
ensure_setting JAMES_SPEECH_ADAPTATION_PATH /var/lib/james/speech-adaptation.json
ensure_setting JAMES_LOCAL_LEARNING_PATH /var/lib/james/local-lessons.json
ensure_setting JAMES_PERSISTENT_MEMORY_PATH /var/lib/james/persistent-memory.json
ensure_setting JAMES_SEARXNG_URL http://127.0.0.1:8888
ensure_setting JAMES_SESSION_MAX_TURNS 3
chown root:ember /etc/james/james.env
chmod 0640 /etc/james/james.env

install -o root -g root -m 0644 \
    "${source_dir}/systemd/james-gateway.service" \
    /etc/systemd/system/james-gateway.service
install -o root -g root -m 0644 \
    "${source_dir}/systemd/piper-james.service" \
    /etc/systemd/system/piper-james.service

if [[ ! -f /opt/james/models/piper/en_GB-northern_english_male-medium.onnx ]]; then
    sudo -u ember /opt/ember/venv/bin/python -m piper.download_voices \
        --data-dir /opt/james/models/piper en_GB-northern_english_male-medium
fi

/opt/ember/venv/bin/python -m compileall -q /opt/james/gateway/james_gateway
systemctl daemon-reload
systemctl enable --now piper-james.service
systemctl enable --now james-gateway.service
systemctl restart piper-james.service
systemctl restart james-gateway.service

echo "Project James gateway installed on port 8090."
echo "The token remains in /etc/james/james.env and was not printed."
