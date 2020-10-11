#!/bin/sh

cd "$(dirname "$0")"

if which python3; then
  PIP=pip3
else
  if which python; then
    pver=$(python -c 'import sys; print(sys.version_info[0])')
    if [ $pver -lt 3 ]; then
      echo "THIS PYTHON IS VERSION $pver, you need at least version 3"
      echo "There are many ways to do this, here's one: https://opensource.com/article/19/5/python-3-default-mac"
      exit 1
    fi
    PIP=pip
  else
    echo "PYTHON DOESN'T SEEM TO BE INSTALLED"
    echo "Here are some ways to install it: https://opensource.com/article/19/5/python-3-default-mac"
    exit 1
  fi
fi

$PIP install -r requirements.txt
touch "_SETUP_RAN_"
exit 0
