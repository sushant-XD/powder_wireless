#!/bin/bash
# Install RAN Tester UE on a POWDER node and, unless the role is "install",
# start the controller.
#
# This directory is the POWDER profile repo (cloned to /local/repository).
# RAN Tester UE is cloned separately to /local/rtue, and the spec and radio
# configs from this repo are copied into that checkout before compose starts.
#
#   install   Docker, UHD, and system_setup.sh only. Nothing is started.
#   ue        install, then start the software UE on this node's B210
#   sniffer   install, then start sni5gect on this node's B210
#   gnb       install, then start the srsRAN gNB (see start-gnb.sh)
#
# The profile calls "ue" and "sniffer" when the autostart parameter is true.
# For a manual experiment, set autostart false (the profile then calls
# "install" only) and run one of the roles above over ssh.

set -euo pipefail

ROLE="${1:-install}"
PROFILE=/local/repository
RTUE=/local/rtue
RTUE_GIT="${RTUE_GIT:-https://github.com/oran-testing/ran-tester-ue.git}"

# install reuired packages
install_packages() {
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y docker.io docker-compose-v2 git uhd-host
  systemctl enable --now docker
  if ! command -v uhd_images_downloader >/dev/null; then
    echo "uhd_images_downloader is missing after installing uhd-host" >&2
    exit 1
  fi
}

# install uhd images
if ! command -v docker >/dev/null || ! command -v uhd_images_downloader >/dev/null; then
  install_packages
fi

if [[ ! -d "$RTUE/.git" ]]; then
  git clone "$RTUE_GIT" "$RTUE"
fi

if [[ ! -d "$RTUE/.uhd_images" ]]; then
  (cd "$RTUE" && ./scripts/system_setup.sh --no-confirm)
fi

mkdir -p "$RTUE/powder/configs"
cp "$PROFILE/spec-ue.yaml" "$PROFILE/spec-sniffer.yaml" "$RTUE/powder/"
cp "$PROFILE/configs/"* "$RTUE/powder/configs/"

if [[ "$ROLE" == "install" ]]; then
  echo "Install finished. Start a role with: sudo $0 ue|sniffer|gnb"
  exit 0
fi

case "$ROLE" in
  ue) SPEC=powder/spec-ue.yaml ;;
  sniffer) SPEC=powder/spec-sniffer.yaml ;;
  gnb)
    exec "$PROFILE/start-gnb.sh"
    ;;
  *)
    echo "Unknown role: $ROLE" >&2
    exit 1
    ;;
esac

cd "$RTUE"
if grep -q '^DOCKER_CONTROLLER_INIT_CONFIG=' .env; then
  sed -i "s|^DOCKER_CONTROLLER_INIT_CONFIG=.*|DOCKER_CONTROLLER_INIT_CONFIG=${SPEC}|" .env
else
  echo "DOCKER_CONTROLLER_INIT_CONFIG=${SPEC}" >> .env
fi

# Controller and InfluxDB only. The NUC has four cores; grafana and the MCP
# server are left stopped so the radio process can have them.
# To bring up the full stack instead:
#   sudo docker compose --env-file .env up -d
docker compose --env-file .env up -d controller
echo "Controller started with ${SPEC}"
