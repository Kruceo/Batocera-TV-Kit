

# Always reset the controller profile to "disabled" on exit, even if this
# launcher is killed/crashes. The EXIT trap alone does not run when the shell
# is terminated by an untrapped SIGTERM, so we re-signal via TERM/INT/HUP.
trap 'echo "profile disabled" > /run/controllerd.cmd' EXIT
trap 'exit' TERM INT HUP

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

# Wait until Firefox dies. Always exit cleanly afterwards: the profile
# reset happens via the EXIT trap, and returning 0 keeps EmulationStation
# from treating a killed Firefox (SIGTERM -> wait status 143) as a crash.
wait $FF_PID
exit 0
