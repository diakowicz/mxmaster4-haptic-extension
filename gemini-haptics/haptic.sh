#!/bin/bash
# Trigger a haptic waveform on MX Master 4 via HapticWebPlugin.
# Usage: haptic.sh <waveform>
# Example: haptic.sh completed

WAVEFORM="${1:-subtle_collision}"
curl -s -X POST -d '' "https://local.jmw.nz:41443/haptic/${WAVEFORM}" >/dev/null 2>&1 || true
