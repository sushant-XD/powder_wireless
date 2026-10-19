#!/bin/bash
# Start an srsRAN gNB on the local B210.
# The POWDER profile does not call this. Uncomment the gNB node in
# profile.py (or run this script by hand) when this experiment should
# bring up the gNB instead of using one that is already on the air.
#
# Cell settings match the RAN Tester configs/srsran/gnb_uhd.yaml: band 3,
# DL ARFCN 368500, 20 MHz. The lab serial number is omitted. Indoor OTA
# B210s are locked to the Octoclock, so the clock source is external.

set -euo pipefail

PROFILE=/local/repository
RTUE=/local/rtue

if [[ ! -d "$RTUE/.uhd_images" ]]; then
  echo "Run boot.sh install first" >&2
  exit 1
fi

docker run --privileged \
  -v /dev/bus/usb:/dev/bus/usb \
  -v "$RTUE/.uhd_images/:/usr/local/share/uhd/images" \
  --env UHD_IMAGES_DIR=/usr/local/share/uhd/images \
  -v "$PROFILE/configs/gnb.yaml:/gnb.yaml" \
  --net host \
  ghcr.io/cueltschey/srsgnb \
  bash -c "gnb -c /gnb.yaml"
