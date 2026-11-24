#!/bin/bash
# Trigger a haptic waveform on MX Master 4 via the Masterowich Logi Options+ plugin.
# Usage: haptic.sh <waveform>
# Example: haptic.sh completed

WAVEFORM="${1:-subtle_collision}"
curl -s -X POST -d '' "http://127.0.0.1:5002/haptic/${WAVEFORM}" >/dev/null 2>&1 || true
