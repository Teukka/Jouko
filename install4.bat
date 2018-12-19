#!/bin/bash  
echo "Ajetaan asennusohjelma 4."
echo "Varmistetaan asetukset."
stty -F /dev/ttyAMA0

echo "Asennetaan MCP3008 AD-muuntimen ajurit ja git"
sudo pip install adafruit-mcp3008
sudo apt update
sudo apt upgrade

echo "Asetetaan kelloasetukset"
sudo systemctl disable systemd-timesyncd.service
sudo apt-get remove ntp

echo "Lisää seuraavan rivin teksti viimeistä edelliseksi riviksi ennen 'exit 0' riviä:"
echo "python /home/pi/jouko/main_loop.py &"

sudo nano /etc/rc.local

echo "Asennus on valmis. Määrittele seuraavaksi haluamasi kommunikaatioasetukset ja ajastukset."
echo "Määrittele asetukset .json -tiedostoihin."
