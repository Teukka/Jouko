#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################

###################### Laitteelta serverille: ##############################
# Aikaleimat (paitsi aikasynk) sekunteina unix-eepokista, UTC-aikaa.
############################################################################

import BTcom;

################################## Tarpeelliset Import ##########################################
import time;
import json;
import datetime;
import os; # set time
import viestinpurku;

# Ladataan asetukset JSON-tiedostoista
# Asetukset jaettu 3 tiedostoon:
# 1 - asetukset.json, - yleiset asetukset kaikille laitteille
# 2 - kommunikaatio.json - kommunikaatio asetukset radioliikenteelle
# 3 - testiasetukset.json - testiasetukset laitteen kehitysvaiheessa

with open('asetukset.json') as json_general_settings_file:
	asetus	= json.load(json_general_settings_file)
with open('kommunikaatio.json') as json_com_settings_file:
	kommunikaatioasetus	= json.load(json_com_settings_file)
with open('testiasetukset.json') as json_testi_settings_file:
	testiasetus	= json.load(json_testi_settings_file)

debugON=testiasetus['test']['debugON'];# True; # kun 1, niin ei nayteta debug-funktion viesteja

def debug(data): # Komento, jolla annetaan palautetta johonkin kanavaan. Nyt tulostetaan data terminaaliin. Voidaan asettaa keskitetysti pois paalta.
	if debugON:
		print (str(data));

Raspi=testiasetus['test']['Raspi']; # TODO voidaan poistaa lopullisesta versiosta. Tarvitaan, kun tarvittava IO ei ole liitetty. - PC-koodausta varten
OhitaValvoja=testiasetus['test']['OhitaValvoja']; # TODO Poista lopullisesta. Testivaiheessa helpottaa, kun ei tarvitse sulkea valvoja-prosesseja.

### Testivaiheessa tarpeen ###
# Tunnistetaan kayttojarjestelma automaattisesti, jolloin muutetaan asetukset automaattisesti.
import platform
kayttis=platform.platform()
debug ("Kayttojarjestelma on: "+str(kayttis))

if "Windows" in kayttis:
	debug("Ohjelmistoa ajetaan Windows-ymparistossa.") 
	Raspi=False; #win
	simuloituMittaus=True;
### Testivaiheessa tarpeen ###

if False:
	import BTcom;
	global viestiBTlaitteelle1; global viestiBTlaitteelle2; global viestiBTlaitteelle3; global viestiBTlaitteelle4;
	viestiBTlaitteelle1=""; viestiBTlaitteelle2=""; viestiBTlaitteelle3=""; viestiBTlaitteelle4=""
	global vastausBTlaitteelta1; global vastausBTlaitteelta2; global vastausBTlaitteelta3; global vastausBTlaitteelta4;
	vastausBTlaitteelta1=""; vastausBTlaitteelta2=""; vastausBTlaitteelta3=""; vastausBTlaitteelta4="";
	BTlaite_lkm=kommunikaatioasetus['BT']['BTlaite_lkm'];

global kelloSynkroituViimeksi; #Alustetaan synkronointiaika tarpeeksi kauas
nykyhetki = datetime.datetime.now();
kelloSynkroituViimeksi = nykyhetki - datetime.timedelta(30); # kuukausi sitten

if Raspi:
	import RPi.GPIO; # RPi.GPIO as GPIO
	# import Adafruit_GPIO as GPIO # vaihtoehtoinen GPIO-kirjasto
	import Adafruit_GPIO.SPI as SPI; 
	import Adafruit_MCP3008; 
	pass

# Communication import #serial # Lora-import # GPRS-import # BT-import
if Raspi:
	import GPIOhallinta; # GPIO:n hallinta ja siihen liittyvat komennot
	import serial; # sarjaliikenne
	ser = serial.Serial(
		port='/dev/ttyAMA0',
		baudrate = 115200,
		parity=serial.PARITY_NONE,
		stopbits=serial.STOPBITS_ONE,
		bytesize=serial.EIGHTBITS,
		timeout=5
		)
	
###### BT -configuraatio #####
#global omaLaiteID; #  nama tiedot conf-tiedostosta
omaLaiteID=kommunikaatioasetus['com']['omaLaiteID'];
# kytkinLaiteID voi olla tama laite tai BT-laite
BTlaiteID1=kommunikaatioasetus['com']['BTlaiteID1'];#5;
BTlaiteID2=kommunikaatioasetus['com']['BTlaiteID2'];#6;
BTlaiteID3=kommunikaatioasetus['com']['BTlaiteID3'];#7; # ylimaaraiset BTlaite-koodit voidaan asettaa samaksi kuin ID1
BTlaiteID4=kommunikaatioasetus['com']['BTlaiteID4'];#8;

############################### Kommunikaation konffaus ########################################
global vilkutetaanPunaistaLedia; # vilkutetaan LEDia yhden syklin ajan (25s), kun yhteys on muodostettu onnistuneesti
vilkutetaanPunaistaLedia=False;

# Reset more variables for Lora
viesti="";
vastaus="";

error=0 ;	# if error=10 then reset the RM186 CHIP
# ------------------- tiedoston kasittely funktioita -----------------------------
	
def clearDataFile(filename):
	open(filename, 'w').close();
	
def readData(filename):
	fileInput = open(filename,"r") ;
	inputData=fileInput.read();
	fileInput.close();
	return inputData;

def writeData(filename,outputData):
	fileOutput = open(filename,"a");
	fileOutput.write(outputData);
	fileOutput.close();
	# usage writeData("tiedostonnimi.txt","datakirjataanfileen")

def overWriteData(filename,outputData): # kun file update - kirjoitetaan yli ettei kokonaisuus korruptoidu
	fileOutput = open(filename,"w");
	fileOutput.write(outputData);
	fileOutput.close();
	# usage writeData("tiedostonnimi.txt","datakirjataanfileen")

# Komentojen suorittaminen kayttojarjestelmatasolla
def ajaOhjelmaOSsudo(ajettavaOhjelma):
	os.system('sudo "%s"' % ajettavaOhjelma);

def ajaOhjelmaOS(ajettavaOhjelma):
	os.system("%s" % ajettavaOhjelma);

def ajaOhjelmaOSpython(ajettavaOhjelma):
	os.system('python "%s"' % ajettavaOhjelma);
	
# ------------------- perus funktioita -----------------------------
def booleanToInt(boolean):
	palauta=0
	if boolean:
		palauta=1
	return palauta;

def checkJSONStr(jsonString):
	try:
		json_object=json.loads(jsonString);
	# except ValueError, e: # old wrong
	except ValueError as e:
		return False
	return True

def checkDictObj(DictObject): # turha aliohjelma - vain jemmassa
	if isinstance(DictObject, dict):
		return True
	else:
		return False

def string_to_byteString(viesti):
	bytesString= str.encode(viesti)
	return bytesString;

#def encrypt_string(hash_string):
#	 sha_signature = \
#		  hashlib.sha256(hash_string.encode()).hexdigest()
#	 return sha_signature
#sha_signature = encrypt_string(hash_string)

def encrypt_string(message): # viestin SHA autentikointi
	## debug("Luodaaan allekirjoitus autentikointiavaimella binaryshakey: {0}".format(binaryshakey));
	dig = hmac.new(binaryshakey, msg=string_to_byteString(message), digestmod=hashlib.sha256).digest()
	shaSignature = base64.b64encode(dig).decode();		# py3k-mode
	return shaSignature;
	
def createSHAsignature(viesti):
	sha_signature = encrypt_string(viesti);
	debug("Luotiiin SHA256signature: " + str(sha_signature));
	#signature={"token":sha_signature} 
	return sha_signature;

def parseServerMessage(viestidata):  # inputtina bytes ja output dict-objekti
	try:
		viestiPurettuna = viestinpurku.pura_viesti(viestidata);
	except Exception as e:
		debug("Ei paluuviestia palvelimelta tai virhe viestia purettaessa: {}".format(e))
		debug("Palvelimen vastaus oli todennakoisesti tyhja viesti.")
		viestiPurettuna = None

	return viestiPurettuna

def getFromServerAndReply():
	OKviestiPalvelimelle="(KaikkiOK)"
	# READ  BTSlaveViestiPalvelimelle.txt
	luettiinPaluuviesti=False;
	paluuViesti=None
	debug("Luetaan palvelimelle lahteva mittausdataviesti tiedostosta - BTSlaveViestiPalvelimelle.txt.")
	try:
		lahtevaViesti=readData("BTSlaveViestiPalvelimelle.txt")
	except:
		lahtevaViesti=OKviestiPalvelimelle; # tiedosto oli jumissa

	 # luetaan UARTISTA mahdollinen viesti
	vastausOhjauslaitteelta=BTcom.BTReceive(lahtevaViesti)

	# Jos vastausOhjauslaitteelta sisaltaa jotain, niin tallennetaan se.
	paluuViesti=parseServerMessage(vastausOhjauslaitteelta)
	
	if paluuViesti!=None:
		# SAVE BTSlaveViestiPalvelimelta.txt
		try:
			debug("Tallennetaan palvelimelta saapunut viesti tiedostoon - BTSlaveViestiPalvelimelta.txt.")
			overWriteData("BTSlaveViestiPalvelimelta.txt",paluuViesti); # samalla tulkitaan mittausdata lahetetyksi.
			luettiinPaluuviesti=True;
		except:
			debug("BTSlaveViestiPalvelimelta - Paluuviestin kirjoittaminen epaonnistui.")
			luettiinPaluuviesti=False;
		
		try:
			debug("Kirjoitetaan (KaikkiOK) uudeksi viestiksi ohjauslaitteelle, sillä oletetaan myös mahdollisen mittausdatan menneen onnistuneesti ohjauslaitteelle.")
			overWriteData("BTSlaveViestiPalvelimelle.txt",OKviestiPalvelimelle); # samalla tulkitaan mittausdata lahetetyksi.
		except:
			debug("BTSlaveViestiPalvelimelle - Kirjoittaminen epaonnistui.")
	return (luettiinPaluuviesti, paluuViesti);
	
#### BTSLAVE UART VSP LOOPPI alkaa ####

if Raspi:
	# synkronoi UART
	BTcom.UARTsyncLaird();

	# Tarkista RM186moodi - rm186test
	vastaus=BTcom.testRM186(); # reply 1=AT CommandMode
	if vastaus==1:
		debug("Laite odottaa pyyntoa kaynnistaa VSPP-ohjelma.")

	# kaynnista BTslaveCOM - VSPP
	BTcom.BTSlaveInit();
	# sitten muuta ei olekaan enaa tehtavissa. Pitaa vain odottaa connectia ja ohjauslaitteen viestia.

while True: # ikuinen looppi
	(luettiinPaluuviesti, paluuViesti)=getFromServerAndReply()
	if luettiinPaluuviesti:
		debug("Palvelinviesti luettu. Seuraavaa ei taida tulla vahaan aikaan. Voitaisiin odotella pidempaan.")
		overWriteData("BTSlaveViestiPalvelimelle.txt",OKviestiPalvelimelle)
		time.sleep(1); 
	time.sleep(1)
