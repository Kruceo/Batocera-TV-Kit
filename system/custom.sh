sleep 5
ORIGINAL="$(realpath .)"
cd /userdata/system/tools
python controllerd.py
cd $ORIGINAL