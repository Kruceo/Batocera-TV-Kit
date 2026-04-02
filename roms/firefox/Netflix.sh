#!/bin/bash

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

# Wait until Firefox dies
wait $FF_PID

echo "profile nothing" > /run/controllerd.cmd