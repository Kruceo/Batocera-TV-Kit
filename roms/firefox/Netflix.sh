#!/bin/bash

# Always reset the controller profile to "disabled" on exit, even if this
# launcher is killed/crashes. The EXIT trap alone does not run when the shell
# is terminated by an untrapped SIGTERM, so we re-signal via TERM/INT/HUP.
trap 'echo "profile disabled" > /run/controllerd.cmd' EXIT
trap 'exit' TERM INT HUP

CONTROLLER=$(echo "$SDL_GAMECONTROLLERCONFIG" | cut -d',' -f2)
CONTROLLER_FILE=$(python /userdata/system/tools/find_controller.py "$CONTROLLER")
echo "controller $CONTROLLER_FILE" > /run/controllerd.cmd

echo "profile netflix" > /run/controllerd.cmd

PROFILE_DIR=~/.config/mozilla/firefox/batocera-profile
mkdir -p $PROFILE_DIR
cat <<EOF > "$PROFILE_DIR/user.js"
user_pref("general.useragent.override", "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0");
EOF

/userdata/system/.dev/apps/firefox/firefox \
  --kiosk \
  --no-remote \
  --profile "$PROFILE_DIR" \
  https://netflix.com &
FF_PID=$!

# Wait until Firefox dies. Always exit cleanly afterwards: the profile
# reset happens via the EXIT trap, and returning 0 keeps EmulationStation
# from treating a killed Firefox (SIGTERM -> wait status 143) as a crash.
wait $FF_PID
exit 0