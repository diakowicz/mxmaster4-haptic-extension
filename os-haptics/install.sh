#!/bin/bash
set -e

DAEMON="$(cd "$(dirname "$0")" && pwd)/haptics_daemon.py"
PLIST_SRC="$(cd "$(dirname "$0")" && pwd)/com.mxmaster4.haptics.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.mxmaster4.haptics.plist"
PYTHON="$(which python3)"

echo "Installing MX Master 4 haptic daemon..."

# Write plist with actual paths
sed "s|DAEMON_PATH|$DAEMON|g" "$PLIST_SRC" \
  | sed "s|/opt/homebrew/bin/python3|$PYTHON|g" \
  > "$PLIST_DST"

# Unload if already loaded
launchctl unload "$PLIST_DST" 2>/dev/null || true

# Load and start
launchctl load -w "$PLIST_DST"

echo ""
echo "Done. Daemon is running in the background."
echo "Logs: tail -f /tmp/mxmaster4-haptics.log"
echo ""
echo "To stop:    launchctl unload $PLIST_DST"
echo "To start:   launchctl load -w $PLIST_DST"
echo "To remove:  launchctl unload $PLIST_DST && rm $PLIST_DST"
