#!/bin/bash

echo "TOTALLY ALPHA UNSTABLE - DON'T RUN THIS"

install_prereqs() {
    # adding gcc and nodejs for additional runtimes
    PACKAGE_LIST="python3-venv redis gcc nodejs default-jdk-headless mono-mcs mono-runtime"
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
