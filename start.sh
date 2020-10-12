#!/bin/sh

cd "$(dirname "$0")"

if [ ! -f "_SETUP_RAN_" ]; then
  ./setup.sh
  setup_exit=$?
  if [ $setup_exit -gt 0 ]; then
    echo "Failed to set up python, see if there's more info above"
    exit $setup_exit
  fi
fi

python3 obsc.py
