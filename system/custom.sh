# just starts controllerd.py
sleep 10
ORIGINAL="$(realpath .)"
cd /userdata/system/tools
python controllerd.py
cd $ORIGINAL