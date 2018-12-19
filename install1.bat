#!/bin/bash  
echo "Ajetaan asennusohjelma 1, joka asentaa tarpeellisia kirjastoja."
echo "Päivitetään käyttöjärjestelmä"
sudo apt update
sudo apt upgrade
echo "Asennetaan tietokanta-ohjelma ja kirjastoja"
sudo apt install sqlite3 libsqlite3-dev
sudo apt install libssl-dev libffi-dev
echo "Asennetaan protobuf kohteisiin: Python3 ja Python2"
sudo apt install python3-protobuf
sudo apt install python-protobuf

echo "Määritelläksesi SPI-väylän - Aja: asennajouko2.bat"
echo "asennajouko2.bat"