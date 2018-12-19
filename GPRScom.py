#!/usr/bin/env python
# -*- coding: utf-8 -*-

# GPRScom.py - communication via GPRS radio
# - GPIO UART communication with the SIM800F GPRS radio is defined in this program component. This component is only used if the SIM800F GPRS radio is in use.
# GPRScom.py - kommunikaatio GPRS-radion kautta
# - GPIO:n kautta tapahtuva UART-kommunikaatio SIM800F GPRS-radion kanssa maaritellaan tassa ohjelmakomponentissa. Tata komponenttia kaytetaan vain, mikali laitteessa on kaytossa SIM800F GPRS -radio.


import serial
import RPi.GPIO as GPIO
import time
import base64
import json
import GPIOhallinta

with open('asetukset.json') as json_general_settings_file:
	asetus	= json.load(json_general_settings_file)
with open('kommunikaatio.json') as json_com_settings_file:
	kommunikaatioasetus	= json.load(json_com_settings_file)
with open('testiasetukset.json') as json_testi_settings_file:
	testiasetus	= json.load(json_testi_settings_file)

debugON=testiasetus['test']['debugON'];# True; # kun 1, niin ei nayteta debug-funktion viesteja
nimi=kommunikaatioasetus['GPRS']['laite_nimi']; # basicAuth asetukset
pw=kommunikaatioasetus['GPRS']['laite_pw']; # basicAuth asetukset
postURL=kommunikaatioasetus['GPRS']['postURL']; # postURL="jouko.smartip.cl:8080/postia"
APN=kommunikaatioasetus['GPRS']['APN']; # #APN = "prepaid.dna.fi"  #APN = "internet"

# Network settings
SERIAL_PORT = "/dev/ttyAMA0" # Raspberry Pi 1 ja # Raspberry Pi 2
#SERIAL_PORT = "/dev/ttyS0"# Raspberry Pi 3, jos ei asetuksilla muuteta (tehtiin nain)

RequestEOLChar="\r\n"
EndOfGPRSCommandChar="\n"; # SIMCOM800
#EndOfGPRSCommandChar="\r\n"; # 4G-versio

#HTTP-mode settings
global postViestiToimitettuPalvelimelle;
postViestiToimitettuPalvelimelle=False;

#Testi-asetukset
hiljainen=False # false --> komentojen kaiku paalla
VERBOSE = True
PORT=443

URLI=postURL

#delays:
writeDelay=1
syncDelay=0.2
readDelay=0.5

# tyhjia alustuksia
viesti=""
request ="";
requestGET="";
requestPOST="";
reply=""
reply2=""
msg=""

# reset variables
laskuri=0;

# define serial port settings
# see import serial: ser.write ser.read ser.readline
ser = serial.Serial(
	port='/dev/ttyAMA0',
	baudrate = 115200,
	parity=serial.PARITY_NONE,
	stopbits=serial.STOPBITS_ONE,
	bytesize=serial.EIGHTBITS,
	timeout=1
	)

##################################################################################
## Perus funk
def debug(data):
	if debugON:
		print ("Debug:--- : " + str(data))
		try:
			if "ERROR" in data:
				msg="ERROR"
				print (" ------------------------ Virhe havaittu sarjaportista luetun perusteella.");
		except:
			debug("Ei ollut muutettavissa string-muotoon - stringable - ei voinut debugata.")

def ATcommand(commandStr, delay):
	ser.write(commandStr+EndOfGPRSCommandChar)
	time.sleep(delay)
	reply = ser.read(ser.inWaiting())
	debug(str(commandStr + " palautti: " + reply))
	return reply;

#################################################################################
## GPRS yhteyden alustaminen funktiot - AT-komentoja

def UARTsync():
	# debug("Synkronoidaan  UART lahettamalla AT-komentoja.\n");
	reply=ATcommand('AT', 0.2);
	reply=ATcommand('AT', 0.2);
	reply=ATcommand('ATI', 0.1);
	debug("Laiteversio on: {0}".format(reply))
	reply=ATcommand('AT', 0.1);
	reply=ATcommand('AT', 0.1);

def UARTsyncFast():
	# debug("Synkronoidaan  UART lahettamalla AT-komentoja.\n");
	reply=ATcommand('AT', 0.1);
	reply=ATcommand('AT', 0.1);
	
def isReady():
	GPIOhallinta.UART_to_SIMCOM();
	UARTsync();
	time.sleep(1)
	reply=ATcommand('AT', 0.5);
	reply2=ATcommand('AT', 0.5);
	vastaus=False
	debug("Eka reply: {0}".format(reply))
	debug("Toka reply: {0}".format(reply2))
	if ("OK" in reply) or ("OK" in reply2):
		vastaus=True;
	return vastaus;

def isReadyTiny():
	vastaus=False
	reply=ATcommand('AT', syncDelay);
	reply2=ATcommand('AT', syncDelay);
	if ("OK" in reply) and ("OK" in reply2):
		vastaus=True;
	return vastaus;

def initGPRS():
	# varsitetaan, etta puskuri on tyhja - in default server passive mode - modify is active
	turha=ser.read(128)
	time.sleep(syncDelay)
	turha=ser.read(128)
	time.sleep(syncDelay)
	
	# modeemin kaiku ON tai OFF
	if hiljainen:
		reply=ATcommand('ATE0', readDelay);
	if not hiljainen:
		reply=ATcommand('ATE1', readDelay);	
		
	# Asetetaan bearer profiili 1
	cmd='AT+SAPBR=3,1,"Contype", "GPRS"'
	reply=ATcommand(cmd, readDelay);
		
	cmd='AT+SAPBR=3,1,"APN","{0}"'.format(APN)
	reply=ATcommand(cmd, readDelay);
	if ("OK" in reply):
		debug ("Bearer maaritelty, ok.")
	
	# Avataan GPRS. # Bearer 1
	cmd="AT+SAPBR=1,1"
	reply=ATcommand(cmd,6); # EMI testauksessa sulketussa tilassa: tama komento aiheuttanee sahkomagneettisen signaalin, mutta ei saa yhteytta tukiasemaan.
	
	# Kysytaan GPRS-tila ja IP-osoite
	cmd="AT+SAPBR=2,1"
	reply=ATcommand(cmd,readDelay); 
	reply2=False;
	if ("OK" in reply):
		debug ("IP-osoite saatu OK.")
		reply2=True;
	return reply2; # palautetaan True kun init onnistui # EMI testauksessa palautetaan False

def queryIPaddress():
	cmd="AT+SAPBR=2,1"
	reply=ATcommand(cmd,readDelay); 
	if ("OK" in reply):
		debug ("IP-osoite saatu OK.")
	return reply;

def closeGPRS():
	# Suljetaan GPRS context
	cmd="AT+SAPBR=0,1"
	reply=ATcommand(cmd, 1);
	return reply;

##################################################################################
### IO-funktiot
def setPowerOn():
	GPIOhallinta.GPRSpaalle();
	debug("Virta paalle ja nukutaan 15 + 3 s")
	time.sleep(15);
	cmd="AT"
	reply=ATcommand(cmd, 3);
	yhteysOK=isReady()
	while (not yhteysOK):
		debug("Kytketaan laitteen virta paalle ja nukutaan 15 s")
		GPIOhallinta.GPRSpois();
		time.sleep(15);
		yhteysOK=isReady();
		if (not yhteysOK):
			GPIOhallinta.GPRSpaalle();
		time.sleep(15);
		yhteysOK=isReady();
		if (not yhteysOK):
			GPIOhallinta.GPRSreset();
		time.sleep(15);
		yhteysOK=isReady();
	
def setPowerOff():
	GPIOhallinta.GPRSpois();
	time.sleep(1)
	
def hardReset():
	GPIOhallinta.GPRSreset();
	time.sleep(10)
	pass;

def setSerTimeout(serTimeout):
	ser = serial.Serial(
		port='/dev/ttyAMA0',
		baudrate = 115200,
		parity=serial.PARITY_NONE,
		stopbits=serial.STOPBITS_ONE,
		bytesize=serial.EIGHTBITS,
		timeout=serTimeout
		)

#################################################################################
## HTTP / GPRS kommunikaatio funktiot
def initHTTP(osoite):
	# Init HTTP service 
	cmd="AT+HTTPINIT"
	reply=ATcommand(cmd, writeDelay);
	
	# Set parameters for HTTP session
	# Enable SSL function 
	cmd='AT+HTTPSSL=1'
	reply=ATcommand(cmd, writeDelay);
		
	# select profile 1 for HTTP service 
	cmd='AT+HTTPPARA="CID",1'
	reply=ATcommand(cmd, writeDelay);
	
	cmd=str('AT+HTTPPARA="URL","'+osoite+'"') # orig
	reply=ATcommand(cmd, 2);

def onkoPostViestiToimitettu():
	global postViestiToimitettuPalvelimelle;
	vastaus=postViestiToimitettuPalvelimelle;
	postViestiToimitettuPalvelimelle=False
	return vastaus;
	
def postHTTP(viesti):
	global postViestiToimitettuPalvelimelle;
	postViestiToimitettuPalvelimelle=False;
	# credentials="laite_nimi:laite_pw"
	credentials=nimi+":"+pw

	auth_header="Authorization: Basic {}".format(base64.b64encode(credentials))
	cmd=str('AT+HTTPPARA="USERDATA","'+auth_header+'"') # orig
	reply=ATcommand(cmd, writeDelay);
	
	# esim. HTTP POST data, jossa koko on 254 Bytes ja datan syottaminen saa kestaa 2000 ms. Komennot syottamisen jalkeen odotetaan 0,5 sekuntia.
	#reply=ATcommand("AT+HTTPDATA=254,2000", 0.5);
	
	reply=ATcommand("AT+HTTPDATA={},2000".format(len(viesti)), 0.5); # Aika voitaisiin asettaa lyhyemmaksi, mutta silla ei ole merkitysta, jos viestin koko on oikein.
		
	# Kirjoitetaan viesti UART:iin, josta SIMCOM on valmiina vastaanottamaan maaritellyn maaran tavuja. DCD on asetettu tilaan 'low'.
	reply=ATcommand(viesti, 3); # poistettu viestista + chr(26)
		
	# Jos OK, SIMCOM on vastaanottanut datan, eika vastaanota enempaa. DCD on asetettu tilaan high.
	
	# aloitetaan HTTPS POST session 
	reply=ATcommand("AT+HTTPACTION=1", 8); # Lahetaan POST-viesti palvelimelle ja odotetaan paluuviestia 8 s.
	# jos +HTTPACTION: 1,200,0 niin 'POST successfully completed'
	if ("1,200," in reply):
		debug ("Viesti meni perille")
		postViestiToimitettuPalvelimelle=True;
		# Luetaan HTTP-palvelimen vastaus
		reply=ATcommand("AT+HTTPREAD", 2);
		debug("Palvelin vastasi: "+str(reply));
	else:
		debug("Viesti ei mennyt perille --> RX ERROR")
		reply=ATcommand("AT+HTTPREAD", 2); # luetaan vastaus turhaan, ettei vastaanottopuskuriin jaa mitaan
		reply="RX ERROR"
	
	return reply;

def getHTTP():
	reply=ATcommand("AT+HTTPACTION=0", 10);
	if ("0,200," in reply):
		debug ("GET-viesti luettu oikein");
	return reply;
	
def termHTTP():
	# Lopetaan HTTP-palvelu # terminate
	reply=ATcommand("AT+HTTPTERM", 1);
		
	if ("ERROR" in reply):
		debug ("HTTP-yhteys on jumissa. Ehka palvelin ei vastannut oikein. RESET.")
		hardReset(); # Virhetilanteessa resetoidaan GPRS-modeemi ja muodostetaan yhteys uudelleen.
		reply2=alustaLaite();
		return reply2;
	return reply;

##########################################################################################################
#### Kutsuttavat isot komennot
def alustaLaite():
	debug ("Resetoidaan GPRS-modeemi");
	setPowerOn();
	
	ser = serial.Serial(SERIAL_PORT, baudrate = 115200, timeout = 5);
	UARTsync();
	if not isReady():
		msg="Radion UART ei vastaa toivotulla tavalla. Suljetaan yhteys.";
		debug (msg);
		return msg;
	UARTsync();
	if isReadyTiny():
		msg="OK"
	return msg
	

def sendHTTPmessageFull(message): # Kokonainen kommunikaatiolooppi. Tata ei talla hetkella kayteta ohjelmaa, vaan tehdaan paloittain.
	debug ("Resetoidaan GPRS-modeemi");
	setPowerOn();
	# debug ("Tehdaan varmistukseksi fyysinen resetti modeemille");
	# hardReset() # fyysinen resetti modeemille - tarpeeton
	
	ser = serial.Serial(SERIAL_PORT, baudrate = 115200, timeout = 5);
	UARTsync();
	if not isReady():
		msg="Radion UART ei vastaa toivotulla tavalla. Suljetaan yhteys.";
		debug (msg);
		return msg;
	UARTsync();
	# Original GRPS INIT	
	debug ("Muodostetaan GPRS-yhteys...");
	reply=initGPRS();
	# init HTTP
	debug ("Alustetaan HTTP protokolla");
	initHTTP(URLI);

	# send HTTP-post
	debug ("Lahetataan POST\n");
	palvelimenvastaus=postHTTP(message);

	debug("palvelimen vastaus on :\n"+str(palvelimenvastaus));		

	# close HTTP service
	debug ("Lopetetaan HTTP\n")
	reply=termHTTP();
	debug ("Suljetaan GPRS-yhteys\n")
	# close GRPS connection
	reply=closeGPRS();

def varmistaRadioEnnenLahetysta():
	ser = serial.Serial(SERIAL_PORT, baudrate = 115200, timeout = 5);
	UARTsyncFast();
	msg="OK"
	if not isReadyTiny():
		msg="ERROR"; # modeemi ei ole valmis. Palautetaan ERROR, jolloin yhteys alustetaan uudelleen.
		debug (msg);
			
	while ("ERROR" in msg):
		debug ("GPRS-radio on jumissa. Valmistellaan yhteys uudelleen. RESET ja alustus.")
		hardReset(); # Virhetilanteessa resetoidaan GPRS-modeemi ja muodostetaan yhteys uudelleen.
		msg=alustaLaite();
	return;

def alustaHTTPEnnenLahetysta():
	# Oletus GRPS ready
	debug ("Alustetaan HTTP protokolla");
	initHTTP(URLI);

def lahetaPOSTjaSulje(message):
	# send HTTP-post
	palvelimenvastaus=postHTTP(message);
	debug("palvelimen vastaus on :\n"+str(palvelimenvastaus));		

	# close HTTP service
	debug ("Lopetetaan HTTP\n")
	reply=termHTTP();
	return palvelimenvastaus;
	
def sendHTTPmessageWhenGPRSConnectedAndReady(message):
	# Oletus GRPS ready
	debug ("Alustetaan HTTP protokolla");
	initHTTP(URLI);

	# send HTTP-post
	debug ("Lahetataan POST\n");
	palvelimenvastaus=postHTTP(message);

	debug("palvelimen vastaus on :\n"+str(palvelimenvastaus));		

	# close HTTP service
	debug ("Lopetetaan HTTP\n")
	reply=termHTTP();
	return palvelimenvastaus;

		
def sendHTTPmessageWhenGPRSConnected(message):
	ser = serial.Serial(SERIAL_PORT, baudrate = 115200, timeout = 5);
	UARTsyncFast();
	msg="OK"
	if not isReadyTiny():
		msg="ERROR"; # modeemi ei ole valmis. Palautetaan ERROR, jolloin yhteys alustetaan uudelleen.
		debug (msg);
			
	while ("ERROR" in msg):
		debug ("GPRS-radio on jumissa. Valmistellaan yhteys uudelleen. RESET ja alustus.")
		hardReset(); # Virhetilanteessa resetoidaan GPRS-modeemi ja muodostetaan yhteys uudelleen.
		msg=alustaLaite();
	
	# Oletus GRPS ready
	debug ("Alustetaan HTTP protokolla");
	initHTTP(URLI);

	# send HTTP-post
	debug ("Lahetataan POST\n");
	palvelimenvastaus=postHTTP(message);

	debug("palvelimen vastaus on :\n"+str(palvelimenvastaus));		

	# close HTTP service
	debug ("Lopetetaan HTTP\n")
	reply=termHTTP();
	return palvelimenvastaus;

def RadioTestOK():
	turha=ser.read(128);
	reply=ATcommand('AT', syncDelay);
	return isReadyTiny();

def softReset(): # Kutsutaan paaohjelmasta. Voidaan laatia erillinen softReset, jos tarpeen. Nyt ajetaan hardReset.
	try:
		GPIOhallinta.GPRSreset();
		time.sleep(1) # turha
	except KeyboardInterrupt:
		debug ("Keskeytetty painamalla ctrl+C");
	except:
		debug ("Keskeytetty jollain ihme tavalla");
	debug ("Kaytettiin modeemia alhaalla.")
	
	reply=isReady();
	return reply;

def EMIsetPowerOn():
	GPIOhallinta.GPRSpaalle();
	debug("Virta paalle ja nukutaan 15 + 3 s")
	time.sleep(7);
	cmd="AT"
	reply=ATcommand(cmd, 3);
	yhteysOK=isReadyTiny()
	if (not yhteysOK):
		debug("Kytketaan laitteen virta paalle ja nukutaan 15 s")
		GPIOhallinta.GPRSpois();
		time.sleep(7);
		yhteysOK=isReadyTiny();
		if (not yhteysOK):
			GPIOhallinta.GPRSpaalle();
		time.sleep(7);
		yhteysOK=isReadyTiny();
		if (not yhteysOK):
			GPIOhallinta.GPRSreset();
		time.sleep(7);
		yhteysOK=isReadyTiny();
	return (yhteysOK)
