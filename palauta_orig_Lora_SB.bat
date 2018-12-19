#!/bin/bash  

echo "Ajetaan komento, joka siirtaa RM186test-ohjelman RM186-radiopiirille."
./UW/MultiDeviceLoader RunOnExit=0 EraseFS=0 FlowControl=0 Baud=115200 DownloadFile=smartBasic/RM186test.uwc Port=/dev/ttyAMA0 Verify=1 Verbose=1
echo "Ajetaan komento, joka siirtaa Lora-kommunikaatio-ohjelman RM186-radiopiirille."
./UW/MultiDeviceLoader RunOnExit=0 EraseFS=0 FlowControl=0 Baud=115200 DownloadFile=smartBasic/cmd.orig.uwc Port=/dev/ttyAMA0 Verify=1 Verbose=1
