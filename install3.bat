#!/bin/bash  
echo "Ajetaan asennusohjelma 3, joka määrittelee UART-väylän."

echo "Määritellään UART-väylä."
sudo systemctl disable hciuart

echo "Kirjaa seuraavat lisäykset config.txt-tiedoston loppuun:"

echo "enable_uart=1"
echo "dtoverlay=pi3-disable-bt"
sudo nano /boot/config.txt

echo "Käynnistetään Raspi uudelleen. Aja uudelleen kaynnistyksen jälkeen asennajouko4.bat"

sleep 2s
echo "3"
sleep 1s
echo "2"
sleep 1s
echo "1"
sleep 1s

sudo reboot now 

