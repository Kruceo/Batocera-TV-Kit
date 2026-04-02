

CONTROLLER=$(echo "$SDL_GAMECONTROLLERCONFIG" | cut -d',' -f2)
CONTROLLER_FILE=$(python /userdata/system/tools/find_controller.py "$CONTROLLER")
echo "controller $CONTROLLER_FILE" > /run/controllerd.cmd

echo "profile youtube" > /run/controllerd.cmd

PROFILE_DIR=~/.config/mozilla/firefox/batocera-profile
mkdir -p $PROFILE_DIR
cat <<EOF > "$PROFILE_DIR/user.js"
user_pref("general.useragent.override","Mozilla/5.0 (Linux; Android 11; Android TV) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36");
EOF

/userdata/system/.dev/apps/firefox/firefox \
  --no-remote \
   --kiosk \
   --profile "$PROFILE_DIR" \
  --enable-features=UseOzonePlatform \
  https://www.youtube.com/tv &
FF_PID=$!

# Wait until Firefox dies
wait $FF_PID

echo "profile disabled" > /run/controllerd.cmd
