#!/bin/bash

echo "DEV ONLY - Use uwsgi + daemontools (or similar) in prod."

PYTHON3=./v0/bin/python3
PACKAGEDIR=./src/multiuserpad

echo "dev setup, starting main/wsmain in the background..."
${PYTHON3} ${PACKAGEDIR}/main.py &
${PYTHON3} ${PACKAGEDIR}/wsmain.py &
echo "...started"
