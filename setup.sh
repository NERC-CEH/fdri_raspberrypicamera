#!/bin/bash

## BEFORE RUNNING

# ssh-keygen -t ed25519 -C “your_email@example.com”
# manual step of adding to Github "deploy keys"
# manual step of adding a device name to a startup script [??]

cd $HOME/FDRI_RaspberryPi_Scripts 
sudo apt-get update && sudo apt-get upgrade -y 
sudo apt-get install python3 python3-picamzero python3-libcamera libcap-dev -y 
sudo cp config/rpi-camera.service /etc/systemd/system/rpi-camera.service
cp camera_startup.sh $HOME/camera_startup.sh
chmod 0775 $HOME/camera_startup.sh
sudo systemctl enable rpi-camera.service 
sudo systemctl start rpi-camera.service

python -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -e . 

# python -m rasberrycam 
