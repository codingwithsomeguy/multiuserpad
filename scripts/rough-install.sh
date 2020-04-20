#!/bin/bash

echo "TOTALLY ALPHA UNSTABLE - DON'T RUN THIS"

install_prereqs() {
    PACKAGE_LIST="python3-venv redis"
    echo "Installing [${PACKAGE_LIST}]"
    sudo apt install -y ${PACKAGE_LIST}

    python3 -m venv v0
    ./v0/bin/pip3 install -r requirements.txt
}

if [[ "${I_AM_CRAZY}" == "yes" ]]; then
    install_prereqs
else
    echo "If you _really_ want to do this, set"
    echo "  I_AM_CRAZY == yes"
fi
