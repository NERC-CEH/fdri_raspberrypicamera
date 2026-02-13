#!/bin/bash

## BEFORE RUNNING

# ssh-keygen -t ed25519 -C “your_email@example.com”
# manual step of adding to Github "deploy keys"
# manual step of adding a device name to a startup script [??]

# Enable I2C interface for watchdog
sudo raspi-config nonint do_i2c 0

# Clone wdt repoistory
rm -rf /home/ukceh/fdri_raspberrypicamera/wdt-rpi/
git clone https://github.com/SequentMicrosystems/wdt-rpi.git
cd /home/ukceh/fdri_raspberrypicamera/wdt-rpi/
sudo make install

# Make ups-debug script executable
chmod +x /home/ukceh/fdri_raspberrypicamera/wdt-rpi/scripts/ups-debug.sh

# Write out current crontab
crontab -l > mycron
# Set up new entry in file
new_entry="* * * * * sudo /home/ukceh/fdri_raspberrypicamera/wdt-rpi/scripts/ups-debug.sh"
if ! crontab -l | fgrep -q "$new_entry"; then
	# echo new cron into cron file
	echo "$new_entry" >> mycron
	# Install new cron file
	crontab mycron
	rm mycron
fi

sudo apt-get update && sudo apt-get upgrade -y 
sudo apt-get install python3 python3-picamzero python3-libcamera libcap-dev -y 
sudo cp /home/ukceh/fdri_raspberrypicamera/config/rpi-camera.service /etc/systemd/system/rpi-camera.service
cp /home/ukceh/fdri_raspberrypicamera/camera_startup.sh $HOME/camera_startup.sh
chmod 0775 $HOME/camera_startup.sh
sudo systemctl enable systemd-timesyncd.service
sudo systemctl enable systemd-time-wait-sync.service
sudo systemctl enable rpi-camera.service 
sudo systemctl start rpi-camera.service

python -m venv --system-site-packages .venv
source .venv/bin/activate
cd /home/ukceh/fdri_raspberrypicamera

# Copy src folder
cp -r ./src/raspberrycam .

# Install requirements
pip install -r requirements.txt
 
# python -m raspberrycam 
