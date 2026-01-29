# manual step of adding to Github "deploy keys"
# manual step of adding a device name to a startup script

# Enable I2C interface for watchdog
sudo raspi-config nonint do_i2c 0

# Clone wdt repoistory
git clone https://github.com/SequentMicrosystems/wdt-rpi.git
cd wdt-rpi/
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

cd $HOME/FDRI_RaspberryPi_Scripts 
sudo apt-get update && sudo apt-get upgrade -y 
sudo apt-get install python3 python3-picamzero python3-libcamera libcap-dev -y 
