#!/bin/bash
# Start Open5GS and an srsRAN gNB on the local B210. Called by boot.sh gnb.
#
# 5GC is srsRAN's docker Open5GS at 10.53.1.2. The gNB is
# ghcr.io/cueltschey/srsgnb at 10.53.1.1, matching configs/gnb.yaml.
# The subscriber is the soft USIM in configs/ue.conf.
#
# First boot docker-builds the Open5GS image from srsRAN's Dockerfile
# (ninja runs inside that build, not on the host). Later boots reuse the image.
# Both containers are detached so the POWDER startup service can finish.

set -euo pipefail

PROFILE=/local/repository
RTUE=/local/rtue
SRSRAN=/local/srsran
SRSRAN_GIT="${SRSRAN_GIT:-https://github.com/srsran/srsRAN_Project.git}"

if [[ ! -d "$RTUE/.uhd_images" ]]; then
  echo "Run boot.sh install first" >&2
  exit 1
fi

modprobe sctp 2>/dev/null || true
sysctl -w net.ipv4.ip_forward=1 >/dev/null

if [[ ! -f "$SRSRAN/docker/open5gs/Dockerfile" ]]; then
  rm -rf "$SRSRAN"
  git clone --depth 1 --filter=blob:none --sparse "$SRSRAN_GIT" "$SRSRAN"
  git -C "$SRSRAN" sparse-checkout set docker/open5gs
fi

export PROFILE RTUE
export SRSRAN_OPEN5GS_CTX="$SRSRAN/docker/open5gs"
export OPEN_5GS_ENV_FILE="$PROFILE/configs/open5gs.env"

cd "$PROFILE"
docker compose -f docker-compose.gnb.yml up -d --wait
echo "Open5GS (open5gs_5gc) and gNB (srsran_gnb) are up"
echo "Logs: sudo docker logs -f open5gs_5gc   or   sudo docker logs -f srsran_gnb"
