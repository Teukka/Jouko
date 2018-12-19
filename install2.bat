#!/bin/bash  
echo "Muuta asetukset: 5 Interfacing Options --> 4 SPI --> Enable"
sudo raspi-config
echo "Käynnistetään Raspi uudelleen. Aja uudelleen kaynnistyksen jälkeen asennajouko3.bat"

sleep 2s
echo "3"
sleep 1s
echo "2"
sleep 1s
echo "1"
sleep 1s

sudo reboot now 
