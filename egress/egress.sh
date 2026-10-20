#!/bin/sh
# Egress-Proxy und internes Netz für Agenten-Container.
# UNGETESTET (21.10.2026): Docker wurde dafür nicht
# gestartet. SQUID_IMAGE selbst wählen, per Digest pinnen;
# der Pfad der Konfiguration hängt vom Image ab.
set -eu
: "${SQUID_IMAGE:?Squid-Image mit Digest angeben}"
SRC="$PWD/squid.conf"
DST=/etc/squid/squid.conf

# 1. Netz ohne Route nach draußen
docker network create --internal \
  --subnet 172.30.0.0/24 agent-netz

# 2. Proxy: im internen Netz und im Standardnetz
docker run -d --name egress --network agent-netz \
  --mount "type=bind,src=$SRC,dst=$DST,readonly" \
  "$SQUID_IMAGE"
docker network connect bridge egress

# 3. Agent oder Testlauf: nur internes Netz plus Proxy
# docker run --rm --network agent-netz \
#   --env HTTPS_PROXY=http://egress:3128 \
#   --env HTTP_PROXY=http://egress:3128 ... IMAGE uv sync
