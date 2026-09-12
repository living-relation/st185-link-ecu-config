#!/usr/bin/env bash
# Idempotent Cloud Agent bootstrap for the ST185 TrackCluster CAN tooling repo.
# Installs the GUI backend needed by the pywebview desktop sender app, then the
# Python dependencies for the bench tool, the sender app, and the RealDash
# automation helpers. Safe to re-run.
set -euo pipefail

cd "$(dirname "$0")/.."

# --- System packages -------------------------------------------------------
# pywebview's GTK backend needs the WebKit2 GObject-introspection bindings and
# the matching runtime library; GTK3 bindings are the pywebview default GUI.
# Everything else (Python 3.12, PyGObject, Xvfb) is already in the base image.
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  gir1.2-webkit2-4.1 \
  libwebkit2gtk-4.1-0 \
  gir1.2-gtk-3.0

# --- Python dependencies ---------------------------------------------------
# No virtualenv: the base image's pip installs into the user site by default.
python3 -m pip install -r bench/requirements.txt
python3 -m pip install -r apps/trackcluster-can-sender/requirements.txt
python3 -m pip install -r rd-build/tools/requirements.txt

echo "TrackCluster environment ready."
