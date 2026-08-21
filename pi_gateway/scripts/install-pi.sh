#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
    echo "Run this installer with sudo." >&2
    exit 1
fi

source_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
test -x /opt/ember/venv/bin/uvicorn
getent passwd ember >/dev/null

install -d -o root -g root -m 0755 /opt/tars/gateway
install -d -o ember -g ember -m 0755 /opt/tars/models/piper
install -d -o ember -g ember -m 0750 /var/lib/tars
install -d -o root -g ember -m 0750 /etc/tars
cp -a "${source_dir}/tars_gateway" /opt/tars/gateway/
install -o root -g root -m 0644 "${source_dir}/requirements.txt" /opt/tars/gateway/requirements.txt

if [[ ! -f /etc/tars/tars.env ]]; then
    token="$(openssl rand -hex 32)"
    umask 0027
    {
        printf 'TARS_TOKEN=%s\n' "${token}"
        printf 'TARS_WHISPER_URL=http://127.0.0.1:8080\n'
        printf 'TARS_PIPER_URL=http://127.0.0.1:5001\n'
        printf 'TARS_OLLAMA_URL=http://127.0.0.1:11434\n'
        printf 'TARS_LLM_PROVIDER=auto\n'
        printf 'TARS_GEMINI_MODEL=gemini-3.5-flash-lite\n'
        printf 'TARS_GEMINI_GOOGLE_SEARCH=true\n'
        printf 'TARS_LLM_FALLBACK_TO_OLLAMA=true\n'
        printf 'TARS_OLLAMA_MODEL=qwen3:1.7b\n'
        printf 'TARS_OLLAMA_THINK=false\n'
        printf 'TARS_WEATHER_LAT=-33.9249\n'
        printf 'TARS_WEATHER_LON=18.4241\n'
        printf 'TARS_WEATHER_PLACE=Cape Town, Western Cape, South Africa\n'
        printf 'TARS_TTS_LENGTH_SCALE=0.94\n'
        printf 'TARS_TTS_NOISE_SCALE=0.76\n'
        printf 'TARS_TTS_NOISE_W_SCALE=0.90\n'
        printf 'TARS_TELEMETRY_ENABLED=true\n'
        printf 'TARS_TELEMETRY_INCLUDE_TEXT=false\n'
        printf 'TARS_TELEMETRY_PATH=/var/lib/tars/telemetry.jsonl\n'
        printf 'TARS_TELEMETRY_MAX_BYTES=10485760\n'
        printf 'TARS_PERSONALITY_PATH=/var/lib/tars/personality.json\n'
        printf 'TARS_SPEECH_ADAPTATION_PATH=/var/lib/tars/speech-adaptation.json\n'
        printf 'TARS_LOCAL_LEARNING_PATH=/var/lib/tars/local-lessons.json\n'
        printf 'TARS_PERSISTENT_MEMORY_PATH=/var/lib/tars/persistent-memory.json\n'
        printf 'TARS_SEARXNG_URL=http://127.0.0.1:8888\n'
        printf 'TARS_SESSION_MAX_TURNS=3\n'
        printf 'TARS_MAX_UTTERANCE_BYTES=1048576\n'
    } >/etc/tars/tars.env
    chown root:ember /etc/tars/tars.env
    chmod 0640 /etc/tars/tars.env
fi

ensure_setting() {
    local key="$1"
    local value="$2"
    if ! grep -q "^${key}=" /etc/tars/tars.env; then
        printf '%s=%s\n' "${key}" "${value}" >>/etc/tars/tars.env
    fi
}

ensure_setting TARS_GEMINI_GOOGLE_SEARCH true
ensure_setting TARS_TTS_LENGTH_SCALE 0.94
ensure_setting TARS_TTS_NOISE_SCALE 0.76
ensure_setting TARS_TTS_NOISE_W_SCALE 0.90
ensure_setting TARS_TELEMETRY_ENABLED true
ensure_setting TARS_TELEMETRY_INCLUDE_TEXT false
ensure_setting TARS_TELEMETRY_PATH /var/lib/tars/telemetry.jsonl
ensure_setting TARS_TELEMETRY_MAX_BYTES 10485760
ensure_setting TARS_PERSONALITY_PATH /var/lib/tars/personality.json
ensure_setting TARS_SPEECH_ADAPTATION_PATH /var/lib/tars/speech-adaptation.json
ensure_setting TARS_LOCAL_LEARNING_PATH /var/lib/tars/local-lessons.json
ensure_setting TARS_PERSISTENT_MEMORY_PATH /var/lib/tars/persistent-memory.json
ensure_setting TARS_SEARXNG_URL http://127.0.0.1:8888
ensure_setting TARS_SESSION_MAX_TURNS 3
chown root:ember /etc/tars/tars.env
chmod 0640 /etc/tars/tars.env

install -o root -g root -m 0644 \
    "${source_dir}/systemd/tars-gateway.service" \
    /etc/systemd/system/tars-gateway.service
install -o root -g root -m 0644 \
    "${source_dir}/systemd/piper-tars.service" \
    /etc/systemd/system/piper-tars.service

if [[ ! -f /opt/tars/models/piper/en_GB-northern_english_male-medium.onnx ]]; then
    sudo -u ember /opt/ember/venv/bin/python -m piper.download_voices \
        --data-dir /opt/tars/models/piper en_GB-northern_english_male-medium
fi

/opt/ember/venv/bin/python -m compileall -q /opt/tars/gateway/tars_gateway
systemctl daemon-reload
systemctl enable --now piper-tars.service
systemctl enable --now tars-gateway.service
systemctl restart piper-tars.service
systemctl restart tars-gateway.service

echo "Project TARS gateway installed on port 8090."
echo "The token remains in /etc/tars/tars.env and was not printed."
