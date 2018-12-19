#!/usr/bin/env python
# -*- coding: utf-8 -*-

# TODO tutki ser timeout asetuksen jarkeva kaytto - setSerTimeout(serTimeout) OK?

import serial
import RPi.GPIO as GPIO
import time
import datetime
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
postURL=kommunikaatioasetus['GPRS']['postURL']; # postURL="jouko.smartip.cl:8080/postia"; # apache2:n kautta toimii 
APN=kommunikaatioasetus['GPRS']['APN']; # #APN = "prepaid.dna.fi"  #APN = "internet"

# Network settings
SERIAL_PORT = "/dev/ttyAMA0" # Raspberry Pi 1 ja # Raspberry Pi 2
#SERIAL_PORT = "/dev/ttyS0"# Raspberry Pi 3, jos ei asetuksilla muuteta (tehtiin nain)

RequestEOLChar="\r\n"
#EndOfGPRSCommandChar="\n"; # SIMCOM800
EndOfGPRSCommandChar="\r\n"; # 4G-versio
EndOfLineChar="\n"; # UART

#HTTP-mode settings
#postURL="jouko.smartip.cl:1880/postia"; # suoraan node-rediin toimii
#postURL="015d7563.ngrok.io/api-0.0.1-SNAPSHOT/v1/gprs/gprs"; # Ilmon palvelin 16.04.2018
#postURL="jouko.smartip.cl/nr/postia" #nginx kautta
#postURL="jouko.smartip.cl/nr2/postia"
#postURL="jouko.smartip.cl/nr3/postia"
getURL="jouko.smartip.cl:1880/sivu"
#postURL="jouko.smartip.cl/nr/postia"
#getURL="jouko.smartip.cl/nr/sivu"
global POSTviesti;
POSTviesti='{"laite_id":13, "teho1": 850, "teho2": 865, "teho3": 855, "rele1": 1, "rele2": 1, "rele3": 1}';
global postViestiToimitettuPalvelimelle;
postViestiToimitettuPalvelimelle=False;

#Testi-asetukset
hiljainen=False # false --> komentojen kaiku paalla
VERBOSE = True
PORT=443

## URLI=postURL
URLI="jouko.smartip.cl"
PORTTI=8080


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
				msg="ERROR" # TODO havaitse ERROR
				print (" ------------------------ Virhe havaittu sarjaportista luetun perusteella.");
		except:
			debug("Ei ollut stringable - ei voinut debugata.")

def ATcommand(commandStr, delay):
	ser.write(commandStr+EndOfGPRSCommandChar)
	time.sleep(delay)
	reply = ser.read(ser.inWaiting())
	debug(str(commandStr + " palautti: " + reply))
	return reply;

def printToUART(commandStr, delay):
	ser.write(commandStr+EndOfLineChar)
	time.sleep(delay)
	reply = ser.read(ser.inWaiting())
	debug(str(commandStr + " palautti: " + reply))
	return reply;


#################################################################################
## GPRS yhteyden alustaminen funktiot - AT-komentoja


def UARTsync():
	# Sync UART connection by sending multiple AT or ATI commands
	reply=ATcommand('AT', 0.2);
	reply=ATcommand('AT', 0.2);
	reply=ATcommand('AT', 0.1);
	reply=ATcommand('ATI', 0.1);
	debug("Laiteversio on: {0}".format(reply))
	reply=ATcommand('AT', 0.1);

def UARTsyncFast():
	# Sync UART connection by sending multiple AT or ATI commands
	reply=ATcommand('AT', 0.1);
	reply=ATcommand('AT', 0.1);
	
def isReady():
	GPIOhallinta.UART_to_SIMCOM();
	UARTsync();
	time.sleep(1)
	# Resetting to defaults
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

def openNET():
	cmd="AT+NETOPEN"
	reply=ATcommand(cmd,readDelay); 
	if ("OK" in reply):
		debug ("4G-verkko on auki")
	return reply;

def openNETvarmistus():
	cmd="AT+NETOPEN?"
	reply=ATcommand(cmd,readDelay); 
	if ("NETOPEN: 1" in reply):
		debug ("4G-verkko on varmasti auki")
	return reply;

def queryIPaddress():
	cmd="AT+IPADDR"
	reply=ATcommand(cmd,readDelay); 
	if ("OK" in reply):
		debug ("IP-osoite OK.")
	return reply;


def initGPRS():
	reply2="ERROR. Ei vastausta"
	# check everything ok
	
	# HUOM - clear buffer - in default server passive mode - xxx zzz - modify is active
	turha=ser.read(128)
	time.sleep(syncDelay)
	turha=ser.read(128)
	time.sleep(syncDelay)
	
	# set echo ON or OFF
	if hiljainen:
		reply=ATcommand('ATE0', readDelay);
	if not hiljainen:
		reply=ATcommand('ATE1', readDelay);	
	
	## avaa netti 
	reply=openNET();
	reply=openNETvarmistus();
	
	reply=queryIPaddress();
	
	if ("OK" in reply):
		debug ("IP address received")
		reply2=True;
	return reply2; # palautetaan True kun init onnistui

def closeGPRS():
	# Close a GPRS context
	cmd="AT+NETCLOSE"
	reply=ATcommand(cmd, 1);
	return reply;

##################################################################################
### IO-funktiot
def setPowerOn():
	GPIOhallinta.GPRSpaalle();
	debug("Virta paalle ja nukutaan 7 + 3 s")
	time.sleep(15);
	cmd="AT"
	reply=ATcommand(cmd, 3);
	yhteysOK=isReady()
	while (not yhteysOK):
		debug("Uudelleen virta paalle ja nukutaan 5 s")
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
	time.sleep(5)
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

def initHTTP():
	
	cmd='AT+NETOPEN'
	reply=ATcommand(cmd, writeDelay);

	cmd='AT+IPADDR'
	reply=ATcommand(cmd, writeDelay);	
	
	cmd='AT+CIPOPEN=0,"TCP","77.240.23.174",8080'
	cmd='AT+CIPOPEN=0,"TCP","{0}",{1}'.format(osoite,PORTTI)
	reply=ATcommand(cmd, writeDelay);
	return reply
	# select profile 1 for HTTP service 
	
	

def initHTTPold(osoite):
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
	
	##	avataan TCP
	cmd='AT+CIPSEND=0,1000'
	reply=ATcommand(cmd, writeDelay);
	
	## luodaan viesti
	credentials="laite_nimi:laite_pw"
	auth_header="Authorization: Basic {}".format(base64.b64encode(credentials))
	cmd=str('AT+HTTPPARA="USERDATA","'+auth_header+'"') # orig
	reply=ATcommand(cmd, writeDelay);
	
	# POST the data whose size is 254 Bytes and the maximum latency time for inputting is 1000 ms. It is recommended to set the latency time long enough to allow downloading all the data. 
	#reply=ATcommand("AT+HTTPDATA=254,2000", 0.5);
	
	reply=ATcommand("AT+HTTPDATA={},2000".format(len(viesti)), 0.5); # check the time needed
		
	# Write message to UART. It is ready to receive data from UART, and DCD has been set to low. 
	reply=ATcommand(viesti+chr(26), 3); # poistettu viestista 
		
	# if OK then All data has been received over, and DCD is set to high. 
	
	# POST session start 
	# reply=ATcommand("AT+HTTPACTION=1", 8); # passing the message to server and back # TODO etsi sopiva delay zzz 10 s # 8 s toimii
	# if +HTTPACTION: 1,200,0 then POST successfully completed
	time.sleep(1)
	cmd="AT"
	reply=ATcommand(cmd,2)
	
	
	if ("1,200," in reply):
		debug ("Viesti meni perille")
		postViestiToimitettuPalvelimelle=True;
		# Read reply the data of HTTP server 
		reply=ATcommand("AT+HTTPREAD", 2);
		debug("Palvelin vastasi: "+str(reply));
	else:
		debug("Viesti ei mennyt perille --> RX ERROR")
		# reply=ATcommand("AT+HTTPREAD", 2); # luetaan vastaus turhaan, ettei vastaanottopuskuriin jaa mitaan
		#reply="RX ERROR"
	
	return reply;

def getHTTP():
	reply=ATcommand("AT+HTTPACTION=0", 10);
	if ("0,200," in reply):
		debug ("GET-viesti luettu oikein");
	return reply;
	
def termHTTP():
	# Terminate HTTP service 
	reply=ATcommand("AT+HTTPTERM", 1);
		
	if ("ERROR" in reply):
		debug ("HTTP-yhteys on jumissa. Ehka palvelin ei vastannut oikein. RESET")
		hardReset(); # Virhetilanteessa resetoidaan GPRS-modeemi ja muodostetaan yhteys uudelleen.
		reply2=alustaLaite();
		return reply2;
	return reply;

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
	# debug ("Resetoidaan GPRS-modeemi");
	# setPowerOn();
	# debug ("Tehdaan varmistukseksi fyysinen resetti modeemille");
	# hardReset() # fyysinen resetti modeemille
	
	ser = serial.Serial(SERIAL_PORT, baudrate = 115200, timeout = 5);
	# UARTsync();
	if not isReady():
		msg="Modem not ready. Closing server conn.";
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
	palvelimenvastaus=postHTTP(POSTviesti);

	debug("palvelimen vastaus on :\n"+str(palvelimenvastaus));		

	# close HTTP service
	debug ("Lopetetaan HTTP\n")
	reply=termHTTP();
	debug ("Suljetaan GPRS-yhteys\n")
	# close GRPS connection
	reply=closeGPRS();
	
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
	##debug ("Lopetetaan HTTP\n")
	## reply=termHTTP();
	return palvelimenvastaus;

def RadioTestOK():
	reply=ATcommand('AT', syncDelay)
	return isReadyTiny();

def softReset():
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

######################### ALUSTA 4G-laite SIMCOM 7500E #######################

def alustaSIMCOMlaite(apn="internet"):
	# UUSIN SEKVENSSI:  ALUSTUS
	cmd='AT+CGDCONT=1,"IP","{0}"'.format(apn)
	reply=ATcommand(cmd, writeDelay)
	cmd='AT+CGDCONT?'
	reply=ATcommand(cmd, writeDelay)
	cmd='AT+CSQ'
	reply=ATcommand(cmd, writeDelay)
	cmd='AT+CREG?'
	reply=ATcommand(cmd, writeDelay)
	cmd='AT+CPSI?'
	reply=ATcommand(cmd, writeDelay)
	cmd='AT+CGREG?'
	reply=ATcommand(cmd, writeDelay)
	cmd='AT+CGSOCKCONT=1,"IP","{0}"'.format(apn)
	reply=ATcommand(cmd, writeDelay)
	cmd='AT+CGSOCKCONT?'
	reply=ATcommand(cmd, writeDelay)
	cmd='AT+CSOCKSETPN=1'
	reply=ATcommand(cmd, writeDelay)
	cmd='AT+CIPMODE=0'
	reply=ATcommand(cmd, writeDelay)
	return reply;
	

# toimii vain vanhalla HTTP protokollalla, jota ei tue mikaan palvelin
def httpGET(osoite="jouko.smartip.cl",portti="8018"):
	#cmd='AT+CHTTPACT=?'
	#reply=ATcommand(cmd, writeDelay)
	
	nykyhetki = datetime.datetime.now();
	
	cmd='AT+CHTTPACT="httpbin.org",80'
	#cmd='AT+CHTTPACT="jouko.smartip.cl",8018'
	# cmd='AT+CHTTPACT="jouko.smartip.cl",8080'
	# cmd='AT+CHTTPACT="{0}",{1}'.format(osoite, portti);
	reply=ATcommand(cmd,0.3)
	
	# cmd2="GET http://jouko.smartip.cl:8018/index.htm HTTP/1.1"
	cmd2="GET /index.htm"
	cmd2="GET /ip HTTP/1.1"
	reply=printToUART(cmd2,0.01)
	
	#cmd3="Host: jouko.smartip.cl"
	cmd3="Host: httpbin.org"
	reply=printToUART(cmd3,0.01)
	
	# cmd4="User-Agent: Apache-HttpClient/4.5.2"
	# reply=printToUART(cmd4,writeDelay)
	
	#cmd5="Content-Lenght: 0"
	#reply=printToUART(cmd5,writeDelay)
	
	# cmd6="origin: 100.68.138.215"
	#reply=printToUART(cmd5,writeDelay)
		
	ctrlZchar=chr(26)
	cmd6=chr(26)
	reply=printToUART(cmd6,0.4)
	
	nykyhetkiUus = datetime.datetime.now();
	
	erotus=nykyhetkiUus-nykyhetki;
	debug("Loppuaika on: {0}".format(nykyhetkiUus));
	debug("Eroa aikaleimojen valilla: {0}".format(erotus));
	return reply;

def httpGetTCP(message="testiviesti"):
	# Oletus 4G ready
	debug ("Avataan yhteys ja tarkastetaan IP-osoite");
	
	# cmd='AT+NETOPEN'
	#reply=ATcommand(cmd, writeDelay);

	cmd='AT+IPADDR'
	reply=ATcommand(cmd, writeDelay);	
	
	debug ("Avataan TCP-yhteys joukon osoitteeseen");
	
	cmd='AT+CIPOPEN=0,"TCP","77.240.23.174",80'
	# cmd='AT+CIPOPEN=0,"TCP","{0}",{1}'.format(osoite,PORTTI)
	reply=ATcommand(cmd, writeDelay);
	
	nykyhetki = datetime.datetime.now();
		
	
	cmd2="GET /nr/sivu  HTTP/1.1"
	cmd3="Host: jouko.smartip.cl"
	cmd4="Content-Type: application/json"
	cmd5="Cache-Control: no-cache"
	
	kokoviesti=cmd2+"\n"+cmd3+"\n"+cmd4+"\n"+cmd5
	
	pituus=len(kokoviesti);
	debug("Viestin pituus on: {0}".format(pituus));
	
	cmd='AT+CIPSEND=0,{0}'.format(pituus)
	
	reply=ATcommand(cmd,1)
	
	reply=printToUART(cmd2,0.2)
	
	reply=printToUART(cmd3,0.2)
	
	reply=printToUART(cmd4,0.2)
		
	reply=printToUART(cmd5,0.2)
	
	ctrlZchar=chr(26)
	cmd6="\n"
	#cmd6=chr(26)
	debug ("Lahetataan GET");
	reply=printToUART(cmd6,3)
	
	nykyhetkiUus = datetime.datetime.now();
	
	cmd='at'
	reply=ATcommand(cmd,1)
	
	cmd7="AT+CIPCLOSE=0"
			
	return reply;	

def httpPostold(message="testiviesti"):
	# Oletus 4G ready
	debug ("Avataan yhteys ja tarkastetaan IP-osoite");
	
	# cmd='AT+NETOPEN'
	#reply=ATcommand(cmd, writeDelay);

	cmd='AT+IPADDR'
	reply=ATcommand(cmd, writeDelay);	
	
	debug ("Avataan TCP-yhteys joukon osoitteeseen");
	
	cmd='AT+CIPOPEN=0,"TCP","77.240.23.174",8080'
	# cmd='AT+CIPOPEN=0,"TCP","{0}",{1}'.format(osoite,PORTTI)
	reply=ATcommand(cmd, writeDelay);
	
	nykyhetki = datetime.datetime.now();
		
	#cmd2="POST /postia  HTTP/1.1"
	#cmd3="Host: jouko.smartip.cl:8080"
	#cmd4="Content-Type: application/json"
	#cmd5="Cache-Control: no-cache"
	
	cmd2="POST /postia HTTP/1.1"
	cmd3="Host: jouko.smartip.cl:8080"
	cmd4="Authorization: Basic bGFpdGVfbmltaTpsYWl0ZV9wdw=="
	cmd5="Cache-Control: no-cache"
	cmd6="Postman-Token: 1484b97c-7740-4091-b78c-92776cfb0fd9"

	cmd7="{ChMI0hwI4BwIvxwYsqKa2AUgBCgB}"

	kokoviesti=cmd2+"\n"+cmd3+"\n"+cmd4+"\n"+cmd5+"\n"+cmd6+"\n"+cmd7
	
	pituus=len(kokoviesti);
	debug("Viestin pituus on: {0}".format(pituus));
	
	cmd='AT+CIPSEND=0,{0}'.format(pituus)
	
	reply=ATcommand(cmd,1)
	
	reply=printToUART(kokoviesti,2)
	
	ctrlZchar=chr(26)
	cmd6="\n"
	#cmd6=chr(26)
	debug ("Lahetataan GET");
	reply=printToUART(cmd6,3)
	
	nykyhetkiUus = datetime.datetime.now();
	
	cmd='at'
	reply=ATcommand(cmd,1)
	
	cmd7="AT+CIPCLOSE=0"
			
	return reply;	

def httpPost(message="testiviesti"):
	# Oletus 4G ready
	debug ("Avataan yhteys ja tarkastetaan IP-osoite");
	
	#cmd='AT+NETOPEN'
	#reply=ATcommand(cmd, writeDelay);

	cmd='AT+IPADDR'
	reply=ATcommand(cmd, writeDelay);	
	
	debug ("Avataan TCP-yhteys joukon osoitteeseen");

	cmd='AT+CHTTPSSTART'
	reply=ATcommand(cmd, 2);	
	
	cmd='AT+CHTTPSOPSE=1,"jouko.smartip.cl",8080'
	md='AT+CHTTPSOPSE=1,"77.240.23.174",8080'
	#reply=ATcommand(cmd, 2);	

	nykyhetki = datetime.datetime.now();

	cmd2="POST /postia HTTP/1.1"
	cmd3="Host: jouko.smartip.cl:8080"
	cmd4="Authorization: Basic bGFpdGVfbmltaTpsYWl0ZV9wdw=="
	cmd5="Cache-Control: no-cache"
	cmd6="Postman-Token: 1484b97c-7740-4091-b78c-92776cfb0fd9"

	cmd7="{ChMI0hwI4BwIvxwYsqKa2AUgBCgB}"

	kokoviesti=cmd2+"\n"+cmd3+"\n"+cmd4+"\n"+cmd5+"\n"+cmd6+"\n"+cmd7
	
	pituus=len(kokoviesti);
	debug("Viestin pituus on: {0}".format(pituus));
	
	cmd='AT+CHTTPSSEND=1,{0}'.format(pituus)
	
	#cmd='at+chttpact="77.240.23.174",8080'	
	reply=ATcommand(cmd,2)
	
	reply=printToUART(kokoviesti,2)
	
	ctrlZchar=chr(26)
	cmd6="\n"
	
	cmd6=chr(26)
	debug ("Lahetataan GET");
	reply=ATcommand(cmd6,3)
	
	nykyhetkiUus = datetime.datetime.now();
	
	cmd='AT+CHTTPSSTATE'
	reply=ATcommand(cmd,1)
	
	#cmd="AT+CHTTPSSTOP"
	#reply=ATcommand(cmd,1)
			
	return reply;	


def httpPostAct(message="testiviesti"):
	# Oletus 4G ready
	debug ("Avataan yhteys ja tarkastetaan IP-osoite");
	
	# cmd='AT+NETOPEN'
	#reply=ATcommand(cmd, writeDelay);

	cmd='AT+IPADDR'
	reply=ATcommand(cmd, writeDelay);	
	
	debug ("Avataan TCP-yhteys joukon osoitteeseen");

	#cmd='AT+CHTTPSSTART'
	#reply=ATcommand(cmd, 2);	
	
	#cmd='AT+CHTTPSOPSE=1,"jouko.smartip.cl",8080'
	#md='AT+CHTTPSOPSE=1,"77.240.23.174",8080'
	#reply=ATcommand(cmd, 2);	

	nykyhetki = datetime.datetime.now();

	cmd2="POST /postia HTTP/1.1"
	cmd3="Host: jouko.smartip.cl:8080"
	cmd4="Authorization: Basic bGFpdGVfbmltaTpsYWl0ZV9wdw=="
	cmd5="Cache-Control: no-cache"
	cmd6="Postman-Token: 1484b97c-7740-4091-b78c-92776cfb0fd9"

	cmd7="{ChMI0hwI4BwIvxwYsqKa2AUgBCgB}"

	kokoviesti=cmd2+"\n"+cmd3+"\n"+cmd4+"\n"+cmd5+"\n"+cmd6+"\n"+cmd7
	
	pituus=len(kokoviesti);
	debug("Viestin pituus on: {0}".format(pituus));
	
	#cmd='AT+CHTTPSSEND=1,{0}'.format(pituus)
	
	cmd='at+chttpact="77.240.23.174",8080'	
	reply=ATcommand(cmd,2)
	
	reply=printToUART(kokoviesti,2)
	
	ctrlZchar=chr(26)
	cmd6="\n"
	
	cmd6=chr(26)
	debug ("Lahetataan GET");
	reply=ATcommand(cmd6,3)
	
	nykyhetkiUus = datetime.datetime.now();
	
	cmd='AT+CHTTPSSTATE'
	reply=ATcommand(cmd,1)
	
	#cmd="AT+CHTTPSSTOP"
	#reply=ATcommand(cmd,1)
			
	return reply;	


def httpGetAct(message="testiviesti"):
	# Oletus 4G ready
	debug ("Avataan yhteys ja tarkastetaan IP-osoite");
	
	# cmd='AT+NETOPEN'
	#reply=ATcommand(cmd, writeDelay);

	cmd='AT+IPADDR'
	reply=ATcommand(cmd, writeDelay);	
	
	debug ("Avataan TCP-yhteys joukon osoitteeseen");

	nykyhetki = datetime.datetime.now();

	cmd2="GET index.htm  HTTP/1.1"
	cmd3="Host: jouko.smartip.cl"
	#cmd3="Host: www.google.com"
	cmd4="Content-Type: application/json"
	cmd5="Cache-Control: no-cache"

	kokoviesti=cmd2+"\n"+cmd3+"\n"+cmd4+"\n"+cmd5+"\n"
	
	pituus=len(kokoviesti);
	debug("Viestin pituus on: {0}".format(pituus));
	
	cmd='at+chttpact="jouko.smartip.cl",8018'	
	reply=ATcommand(cmd,2)
	
	reply=printToUART(kokoviesti,2)
	
	ctrlZchar=chr(26)
	cmd6="\n"
	
	cmd6=chr(26)
	debug ("Lahetataan GET");
	reply=ATcommand(cmd6,3)
	
	nykyhetkiUus = datetime.datetime.now();
	
	cmd='AT+CHTTPSSTATE'
	reply=ATcommand(cmd,1)
	
	#cmd="AT+CHTTPSSTOP"
	#reply=ATcommand(cmd,1)
			
	return reply;	
	
def httpGET(osoite="jouko.smartip.cl",portti="8018"):
	#cmd='AT+CHTTPACT=?'
	#reply=ATcommand(cmd, writeDelay)
	
	nykyhetki = datetime.datetime.now();
	
	cmd='AT+CHTTPACT="httpbin.org",80'
	#cmd='AT+CHTTPACT="jouko.smartip.cl",8018'
	# cmd='AT+CHTTPACT="jouko.smartip.cl",8080'
	# cmd='AT+CHTTPACT="{0}",{1}'.format(osoite, portti);
	reply=ATcommand(cmd,0.3)
	
	# cmd2="GET http://jouko.smartip.cl:8018/index.htm HTTP/1.1"
	cmd2="GET /index.htm"
	cmd2="GET /ip HTTP/1.1"
	reply=printToUART(cmd2,0.01)
	
	#cmd3="Host: jouko.smartip.cl"
	cmd3="Host: httpbin.org"
	reply=printToUART(cmd3,0.01)
	
	# cmd4="User-Agent: Apache-HttpClient/4.5.2"
	# reply=printToUART(cmd4,writeDelay)
	
	#cmd5="Content-Lenght: 0"
	#reply=printToUART(cmd5,writeDelay)
	
	# cmd6="origin: 100.68.138.215"
	#reply=printToUART(cmd5,writeDelay)
		
	ctrlZchar=chr(26)
	cmd6=chr(26)
	reply=printToUART(cmd6,0.4)
	
	nykyhetkiUus = datetime.datetime.now();
	
	erotus=nykyhetkiUus-nykyhetki;
	debug("Loppuaika on: {0}".format(nykyhetkiUus));
	debug("Eroa aikaleimojen valilla: {0}".format(erotus));
	return reply;
	
	
	
# reply=initGPRS()
# reply=sendHTTPmessageWhenGPRSConnected("message");


# VAIHE 1 - alustaminen
# reply=alustaSIMCOMlaite("internet")

# VAIHE 2 - http GET
#reply=httpGET(osoite="jouko.smartip.cl",portti="8018");
#reply=httpGET(osoite="jouko.smartip.cl",portti="8080");

# reply=httpGET(osoite="httpbin.org",portti="80");


# reply=httpPost()
reply=httpGetAct();
