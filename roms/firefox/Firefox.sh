#!/bin/bash

export HOME=/userdata/system
export MOZ_DISABLE_RDD_SANDBOX=1
export MOZ_DISABLE_CONTENT_SANDBOX=1

cd /userdata/system/.dev/apps/firefox
exec ./firefox
