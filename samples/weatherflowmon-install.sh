#!/bin/sh
sudo systemctl stop weatherflowmon

echo "Installing Weatherflow Library"
pip3 install -e ./..

echo "Copying Samples"
sudo mkdir -p /etc/weatherflow-tools
sudo mkdir -p /opt/weatherflow-tools
sudo cp -f weatherflowmon.py /opt/weatherflow-tools/
sudo cp -n weatherflowmon.config /opt/weatherflow-tools/config.json

echo "Configuring Service..."
sudo cp weatherflowmon.service /lib/systemd/system/weatherflowmon.service
sudo systemctl daemon-reload
sudo systemctl enable weatherflowmon.service
sudo systemctl restart weatherflowmon.service
sudo systemctl status weatherflowmon.service
