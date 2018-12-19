#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################

OhitaAlunTauko=True;

###################### Serverilta laitteelle: ##############################
# DONE - checkMessageType(replyMessage) --> handleServerReply(replyMessage) 
###################### Laitteelta serverille: ##############################
# Aikaleimat (paitsi aikasynk) sekunteina unix-eepokista, UTC-aikaa.
############################################################################

################################## Tarpeelliset Import ##########################################
#import sqlite3; # tuodaan katkoSQL.py
#import threading; # tuodaan katkoSQL.py
import time;
import json;
import datetime;
#import math; # sqrt # tuodaan mittausMCP3008.py
import os;   # set time

os.chdir("/home/pi/raspi/"); # asetetaan tyoskentelyhakemisto, jotta komento voidaan ajaa helposti eri polusta

try:
	import queue # Integrity
except ImportError:
	import Queue as queue;

# import re; # tuodaan viestinpurku.py
import hmac;
import hashlib;
import base64;
import binascii;
import viestinpurku; #jossa import laiteviestit_pb2
import katkoSQL; # katkojen hallinta ja SQL-tietokanta

# vanha # with open('config.json') as json_settings_file:
# vanha #	asetus	= json.load(json_settings_file)

# Asetukset jaettu 3 tiedostoon:
# 1 - asetukset.json, - yleiset asetukset kaikille laitteille
# 2 - kommunikaatio.json - kommunikaatio asetukset radioliikenteelle
# 3 - testiasetukset.json - testiasetukset laitteen kehitysvaiheessa

with open('asetukset.json') as json_general_settings_file:
	asetus	= json.load(json_general_settings_file)
with open('kommunikaatio_4G.json') as json_com_settings_file:
	kommunikaatioasetus	= json.load(json_com_settings_file)
with open('testiasetukset.json') as json_testi_settings_file:
	testiasetus	= json.load(json_testi_settings_file)

# ladattuihin muuttujiin viitataan:
# kommunikaatioasetus['com']['muuttujan_nimi'] , kun kommunikaatio-asetukset
# kommunikaatioasetus['GPRS']['muuttujan_nimi'] , kun GPRS-kommunikaatio-asetukset
# asetus['general']['muuttujan_nimi'] , kun yleiset asetukset
# testiasetus['test']['muuttujan_nimi'] , kun testi-asetukset

Raspi=testiasetus['test']['Raspi']; # palauta - TODO poista lopullisesta - PC-koodausta varten
debugON=testiasetus['test']['debugON'];# True; # kun 1, niin ei nayteta debug-funktion viesteja

#### SET COM HERE ############################################################################################################################## -- ##
# -------------------- Laiteversion konffaus -----------------------
GPRSMode = kommunikaatioasetus['com']['GPRSMode']; # True; # 1, jos GPRS-COMM-laite
LoraMode = kommunikaatioasetus['com']['LoraMode']; # False; # 1, jos Lora-laite
BTmode = kommunikaatioasetus['com']['BTmode'];   # True, jos BT-laite GPRS:n alaisuudessa

TurboMode = kommunikaatioasetus['com']['TurboMode'];   # True, jos Turbo-Jouko

BTslaveMode = kommunikaatioasetus['com']['BTslaveMode'];   # True, jos tama on BT-orjalaite. Huom! oma looppi

# --------------------------------------- AJASTUKSET ---------------------------# TODO lue asetukset tiedostosta
purskeidenLukemisVali=asetus['general']['purskeidenLukemisVali']; # 30 ; # 30 s Mittaustiheys ka. varten # TODO mittaa aika RASPI1
mittausPurskeita=asetus['general']['mittausPurskeita'];# 10 kpl 30 sekunnin mittauksia 5 minuutin keskiarvoon
global mittauksiaTallennetaan; # HUOM TASSA alustetaan GPRS-syklin pituus (n x 5 min)
mittauksiaTallennetaan=asetus['general']['mittauksiaTallennetaan'];# 6 kpl 5 minuutin keskiarvoja tallennetaan ennen muuta toiminta # TAI 2 kpl jos 10 min sykli 
mittauksiaSekunnissa=asetus['general']['mittauksiaSekunnissa'];# 1596; # 183 Laiteriippuvainen eli monta mittausta ehtii lukea sekunnissa

syklinPituusKorjaus=93; # 93ms=50ms+43ms # Kalibroitu viive 2vrk mittauksilla 26.9.2018 # 50 ms Oletetaan kuinka paljon aikaa kuluu, kun ajastus ei ole kaynnissa (eli syklin ulkopuolella - vanhasta uuteen sykliin siirtyessa.)

#### SET HERE - TEST-SETTINGS - TODO remove lopullisesta ######################################################################################## -- ##
# --------------------------------------- Fake-COM-mode ---------------------------
PCMode = testiasetus['test']['PCMode'];   # True, jos BT-laite GPRS:n alaisuudessa
fakeMode = testiasetus['test']['fakeMode']; # True; # if True, simulates fake -communication - And server sending messages random control messages
global fakeReplyMode;
global fakeTimeSpeedUp
fakeReplyMode=testiasetus['test']['fakeReplyMode']; #True
fakeTimeSpeedUp=testiasetus['test']['fakeTimeSpeedUp']; #True


def printtaaAikaleima(aikaleimaIn):
	kelloJaPaiva=datetime.datetime.fromtimestamp(
		int(aikaleimaIn)
		).strftime('%Y-%m-%d %H:%M:%S');
	print("- Mittausten aikaleima on: {0} - pwm ja time: {1}".format(aikaleimaIn, kelloJaPaiva)
	)

if fakeTimeSpeedUp:
	global fakeStarttiAika;
	global fakeKierrosLaskuri;
	fakeStarttiAika = int(round(time.time())); # timestamp in s 
	fakeKierrosLaskuri=0;
	
	luodaanVanhaaDataa=testiasetus['test']['luodaanVanhaaDataa'];
	if luodaanVanhaaDataa: 
		mitenVanhaaVrk=testiasetus['test']['mitenVanhaaVrk']; # montako paivaa menneisyydesta aloitetaan
		mitenVanhaaTunnit=testiasetus['test']['mitenVanhaaTunnit']; # montako paivaa menneisyydesta aloitetaan
		# mitenVanhaaTunnit=1; # mitenVanhaaVrk=0; 
	if luodaanVanhaaDataa:
		fakeStarttiAikaOrig = int(round(time.time())); # timestamp in s		
		print("--- Oikeakellonaika alkutilanteessa ---")
		printtaaAikaleima(fakeStarttiAikaOrig);
		
		# pudotetaan viikko alkuajasta
		tuntiSekunteina=60*60;
		vrkSekunteina=24*tuntiSekunteina;
		
		fakeStarttiAika= fakeStarttiAikaOrig-(mitenVanhaaVrk*vrkSekunteina)-(mitenVanhaaTunnit*tuntiSekunteina);
		print("--- Feikattu kellonaika alkutilanteessa ---")
		printtaaAikaleima(fakeStarttiAika);
		

# -------------------- Kommunikaation testausasetuksia -----------------------
LoraJoinedAtStart=testiasetus['test']['LoraJoinedAtStart']; #False; # False - default # Lora JOINED when START - skip init and JOIN # TODO korvaa RM186test -komennolla
GPRSJoinedAtStart=testiasetus['test']['GPRSJoinedAtStart']; #False; # False - default # GPRS JOINED when START - skip init

viestiPakataan=testiasetus['test']['viestiPakataan']; #True; # False;  # True - default   # protobuf pakkaus kaytossa

# -------------------- Mittauksen testausasetuksia -----------------------
simuloituMittaus=testiasetus['test']['simuloituMittaus']; #True; # False - default # True, niin luetaan MCP33008-mittauksia
saveData=testiasetus['test']['saveData']; #True

if (not Raspi): # yhdistetty PC-asetukset testauksen helpottamiseksi 
	simuloituMittaus=True;
	GPRSMode = False # True; # 1, jos GPRS-COMM-laite
	TurboMode = False # True; # 1, jos 4G-laite
	LoraMode = False # False; # 1, jos Lora-laite
	BTmode = False;   # True, jos BT-laite GPRS:n alaisuudessa
	
if simuloituMittaus:
	import mittausSimulaattori; # testivaihetta varten random-mittauksia generoiva simulaattori

if PCMode:
	import PCcom;
	
# -------------------- debug-asetuksia -----------------------
kerroAsetukset=testiasetus['test']['kerroAsetukset']; # True; # kun 1, niin naytetaan laite-asetukset
ikuisuusRajoitettu=testiasetus['test']['ikuisuusRajoitettu']; #True; # # todo remove lopullisesta
ikuisuudenRajoitettuKesto=testiasetus['test']['ikuisuudenRajoitettuKesto']; #1; # koko syklien toistaminen x kertaa
kommunikaatioLooppiKierroksia=testiasetus['test']['kommunikaatioLooppiKierroksia']; #1 # montako '30 minuutin' (tai '10 minuutin') kierrosta/viestia kommunikoidaan palvelimelle --> sen jalkeen testausta tms

# testiasetus['test'][' ']; #
#### TEST-SETTINGS - END  ######################################################################################## -- ##

import random; # tarvitaan kaynnistykseen satunnainen viive - sahkokatkojen takia 


# fakeMODE-settings
global fakePaluuViestiTyyppi;
if fakeMode:
	import FAKEcom; # palvelinkommunikaation simulaattori - TODO remove lopullisesta
	randomViesti=random.randint(1, 8); # arvotaan viesti
	fakePaluuViestiTyyppi=4;
	#fakePaluuViestiTyyppi=randomViesti; # tai valitse: 3,4,5,7,8,9
	# tyyppi 11 --> katko halutulla ID:lla

def debug(data):
	# Komento, jolla annetaan palautetta johonkin kanavaan. # TODO Clear when ready.
	# Nyt tulostetaan data UARTiin.	
	if debugON:
		print (str(data));


if Raspi:
	import RPi.GPIO; # RPi.GPIO as GPIO
	#### GPIO.setup(channel, GPIO.OUT, initial=GPIO.HIGH) # maaritellaan kanaville alkutilat
	# Tuodaan - Import SPI library (for hardware SPI) and MCP3008 library.
	# import Adafruit_GPIO as GPIO
	import Adafruit_GPIO.SPI as SPI; 
	import Adafruit_MCP3008; 
	pass

# Communication import #serial # Lora-import # GPRS-import # BT-import
if Raspi:
	import GPIOhallinta
	# - serial communication
	import serial
	# 1a. communicate Laird RM186
	import LORAcom; # UART-komennot Lora-radion kayttoon  
	# 1b. communicate SIMCOM800F GSM
	import GPRScom; # UART-komennot GSMradion kayttoon 
	import Turbocom; # UART-komennot GSMradion kayttoon 
	import mittausMCP3008 # mittausten lukeminen SPI-vaylan kautta


############################### Kommunikaation konffaus ########################################
if Raspi:
	#define serial port settings # see import serial: ser.write ser.read ser.readline
	ser = serial.Serial(
		port='/dev/ttyAMA0',
		baudrate = 115200,
		
		parity=serial.PARITY_NONE,
		stopbits=serial.STOPBITS_ONE,
		bytesize=serial.EIGHTBITS,
		timeout=5
		)

# IF GPRS - setting
shakey=kommunikaatioasetus['com']['shakey'];
binaryshakey=kommunikaatioasetus['com']['binaryshakey'];
APN=kommunikaatioasetus['GPRS']['APN'];  # 'prepaid.dna.fi'; # VPNsetting ='prepaid.dna.fi'; OR 'internet' --> 'GPRScom.py tiedostossa

###### BT -configuraatio #####
#global omaLaiteID; # TODO luetaan nama tiedot conf-tiedostosta
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
global sendFailedCountToday, sendFailedCountInRow, sendSucceedCountInRow
sendFailedCountToday=0;
sendFailedCountInRow=0;
sendSucceedCountInRow=0;

error=0 ;	# if error=10 then reset the RM186 CHIP

# ------------------------------------------------------------------#

# Asetetaan ohjattavat Raspin pinnit
katkoOhjaus=0; # 0 = ei katkoa eli rele johtaa; 1 = katko paalla eli rele vedetaan auki ja virta katkaistaan

# -------------------- MCP3008 - IO luku ja kalibroinnnit ----------------------- # TODO luetaan asetukset tiedostosta?
# tallennusVali = purskeidenLukemisVali * mittausPurskeita = 300 # 10 x 30 s eli aika joka odotetaan ennen uutta tallennuskierrosta

mittausKierroksenKestoSekunteina = mittausPurskeita * purskeidenLukemisVali; # 300 # old mittausKierroksenKestoSekunteina = mittausKierroksenKestoMinuutteina * 60 # 5 * 60 = 300
mittausKierroksenKestoMinuutteina = int(round(mittausKierroksenKestoSekunteina/60)) # 5 # minuuttia
kommunikaatioValinPituus = mittauksiaTallennetaan * mittausKierroksenKestoMinuutteina ; # 30 minuuttia. mittauksia tallennetaan x 5 minuutti

global odoteltuLiikaaAiemmin;
odoteltuLiikaaAiemmin=0; # muuttuja, jonka avulla tasaataan syklien pituus tasan 30 minuuttiin

if kerroAsetukset:
	debug("------------------------- config.JSON-tiedoston asetukset  ---------------------------------------------")
	debug(asetus);
	debug("------------------------- keskeiset asetukset parsittuna ---------------------------------------------")
	debug ("MittausPurskeiden lukemisvali on  : " + str(purskeidenLukemisVali) + " s. Huom. vrt. oletus 30.");
	debug ("mittausPurskeita on         : " + str(mittausPurskeita) + " Huom. vrt. oletus 10.");
	debug ("Mittauksia tallennetaan     : " + str(mittauksiaTallennetaan) + " ennen kommunikaatiota. Huom. vrt. oletus 6.");
	debug ("Mittauksia sekunnissa on    : " + str(mittauksiaSekunnissa) + " Huom. vrt. oletus R1 = 183.");
	if GPRSMode:
		debug("GPRS-COMM-laite SIMCOM 800F kaytossa");
	if TurboMode:
		debug("4G-laite SIMCOM 7500E kaytossa");
	if LoraMode:
		debug("Lora-kommunikaatio kaytossa");
	if BTmode:
		debug("BT-kommunikaatio kaytossa eli BT-laite on taman GPRS-laitteen alaisuudessa");
	if LoraJoinedAtStart:
		debug("TESTIASETUS: Oletetaan Lora-laite on jo liittynyt verkkoon.");
	if GPRSJoinedAtStart:
		debug("TESTIASETUS: Oletetaan GPRS-laite on jo liittynyt verkkoon.");
	debug("-------------------------------------------------------------------------------------------------")

# R-zero n.297 mittausta 
# R1 n.183 mittausta vaihtelee 170-190 mittausta sekunnissa --> 3,4 naytetta jaksossa
# n. R3 n. 1800 kirjoitustapahtumaa sekunnissa (hieman yli)
# n. 600 kirjoitustapahtumaa sekunnissa (hieman yli)

# -------------------------------------------------------------------

# -------------------- Alustetaan muuttujia -------------------------

global tallennuksia; # turha?
tallennuksia=0;
global paivitaSofta; # Tarkastetaan mittausten palvelimelle lahetyksen jalkeen.
paivitaSofta=False; # bitti joka nousee ylos, kun softa on ladattu ja koostettu valmiiksi. 


# muita muuttujia
global katkoSaieAlkuun;
global katkoSaieKesto;

katkoSaieAlkuun=0;
katkoSaieKesto=0;

replyMessageFromServer="";
erotus=0;

katkoID=0;
katkoLaiteID=0;
katkonAlku=0;
katkonLoppu=0;
katkonAlkuun=0;
katkonKesto=0;

# -------------------------------------------------------------------

# update variables # define split variables
splitFolder="splittedUpdateFile";
splitSize=128;
joinedFile="jouko.uwf";
fileParts=0;

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
#    sha_signature = \
#        hashlib.sha256(hash_string.encode()).hexdigest()
#    return sha_signature
#sha_signature = encrypt_string(hash_string)

def encrypt_string(message): # viestin SHA autentikointi
	debug("binaryshakey");
	dig = hmac.new(binaryshakey, msg=string_to_byteString(message), digestmod=hashlib.sha256).digest()
	shaSignature = base64.b64encode(dig).decode();      # py3k-mode
	return shaSignature;
	
def createSHAsignature(viesti):
	sha_signature = encrypt_string(viesti);
	debug("Luotiiin SHA256signature: " + str(sha_signature));
	#sigu={"token":sha_signature} 
	return sha_signature;

def parseServerMessage(viestidata):  # inputtina bytes ja output dict-objekti
	try:
		viestiPurettuna = viestinpurku.pura_viesti(viestidata);
	except Exception as e:
		debug("Virhe viestia purettaessa: {}".format(e))
		viestiPurettuna = None
	
#	if fakeMode: # test-settings: TODO remove lopullisesta
#		viestiPurettuna=viestidata;
#		writeData("dataa.txt",str(viestidata))			
	
#	if not fakeMode:	
#		writeData("heksaa.txt",str(binascii.hexlify(viestidata)))
	
	return viestiPurettuna

################# RM186 SmartBasic Integrity hallinta #################################
global integrityLaskuri; integrityLaskuri=0;
global q; 

q = queue.Queue(); 
for i in range(5): # alustetaan jono tayteen vuorottelevia 0 ja 1
	q.put(1);
	q.put(0);
	## debug(list(q.queue))
global alustettuJono; 
alustettuJono=q;
alustettuLista=(list(alustettuJono.queue));

def testaaIntegrityJono():
	testiTulos=False;
	ykkoset=0;
	lista=list(q.queue); # listaksi
	debug("Testataan Laird-integrity. Jono on nyt: {0}".format(lista));
	for x in lista:
		if x==1:
			ykkoset+=1;
	print("Ykkoset on {0}".format(ykkoset))
	if ykkoset>3 and ykkoset<7:
		testiTulos=True;
	return testiTulos;
		
def hallitseIntegrity():
	integrityOK=False;
	global integrityLaskuri;
	global q;
	integrityLaskuri+=1;
	if integrityLaskuri>1999:
		integrityLaskuri=1000; #palautetaan laskuri pienenpaan arvoon

	try:
		integrityTilaNyt=GPIOhallinta.lueLORAintegrity();
		q.get(); #poistetaan jonosta yksi
		q.put(integrityTilaNyt);
		integrityOK=testaaIntegrityJono()
	except Exception as e:
		debug("Virhe jonoa paivitettaessa: {}".format(e))
		q=alustettuJono;
		integrityOK=True; 
	
	if integrityLaskuri<10: # ohitataan ensimmaiset 10 arvoa
		integrityOK=True; # ("Alussa viela. Kaikki arvot hyvaksytaan.")
	
	return integrityOK;
################# RM186 SmartBasic Integrity hallinta #################################

################# Palvelimelta saapuvien viestien vaatimien toimenpiteiden toteuttaminen - funktioita #################################

#viestiTyyppi=3; # kelloajan synkronointiviesti
			
def doTimeSynk(erotus):
	nykyhetki = datetime.datetime.now();
	debug ("nykyhetki:"); debug(nykyhetki);
	# erotus = TP-aika - raspin_aika
	korjattuAika = nykyhetki + datetime.timedelta(milliseconds=erotus);
	debug ("korjattuAika: "); debug (korjattuAika);
	debug ("Setting new date: (check time-auto-update is OFF)");
	os.system('sudo date -s "%s"' % korjattuAika);
	nykyhetki2 = datetime.datetime.now();
	debug ("Uusi kellonaika:");
	debug (nykyhetki2);
	
def doTimeSynkDemo(erotus):
	debug("pyydetty kellon siirtoa: " + str(erotus)+". Poista funktion nimesta 'Demo', niin kello liikkuu oikeasti.");

############################## -- Katkojen hallinta -- ##############################
#viestiTyyppi=4; # katkoAlkaa viesti

global katko1SaieAjossaOdotus; katko1SaieAjossaOdotus=0;
global katko1SaieAjossaKatko; katko1SaieAjossaKatko=0;

# jos halutaan kaksi katkoa jonoon: # tuplataan katkojono - turha - ei tarpeen, koska tietokanta
global katko2SaieAjossaOdotus; katko2SaieAjossaOdotus=0;
global katko2SaieAjossaKatko; katko2SaieAjossaKatko=0;

#viestiTyyppi=5; # katkon esto viesti



		
############################## -- paivitysten hallinta -- ##############################

#viestiTyyppi=7; # paivitys alkaa viesti
#viestiTyyppi=8; # paivitys saapuu viesti

def join(source_dir, dest_file, read_size):
	# Create a new destination file
	output_file = open(dest_file, 'wb');
	# Get a list of the file parts
	parts = os.listdir(source_dir);
	# Sort them by name (remember that the order num is part of the file name)
	parts.sort();
	# Go through each portion one by one
	for file in parts:
		# Assemble the full path to the file
		path = os.path.join(source_dir, file);
		# Open the part
		input_file = open(path, 'rb');
		while True:
			# Read all bytes of the part
			byteData = input_file.read(read_size);
			# Break out of loop if we are at end of file
			if not byteData:
				break
			# Write the bytes to the output file
			output_file.write(byteData);
		# Close the input file
		input_file.close();
	# Close the output file
	output_file.close();
		
#viestiTyyppi=9; # paivitys loppuu viesti


def updateSmartBasic():
	tyhjennysOnnistui=LORAcom.tyhjennaRM186flash();
	if tyhjennysOnnistui:
		debug("Paivitetaan RM186-modulin Smart Basic -ohjelmisto.");
		if GPRSMode:
			ajettavaOhjelma="/home/pi/raspi/UW/R1_lataa_laite2_SB.bat"; # Central-BT, cmd-CE-BT, VSP2
		if TurboMode:
			ajettavaOhjelma="/home/pi/raspi/UW/R1_lataa_laite2_SB.bat"; # Central-BT, cmd-CE-BT, VSP2
		if LoraMode:
			ajettavaOhjelma="/home/pi/raspi/UW/R1_lataa_laite2_SB.bat"; # Central-BT, cmd-CE-BT, VSP2
		if BTmode:
			ajettavaOhjelma="/home/pi/raspi/UW/R1_lataa_laite1_SB.bat"; # Peripheral, cmd-no-BT, VSP1
			
			
		# ajaOhjelmaOS(ajettavaOhjelma);
		try:
			ajaOhjelmaOSsudo(ajettavaOhjelma);
		except:
			# Tanne ei pitaisi koskaan tulla, silla talloin paivitysprosessi on toteutettu puuttteellisesti.
			debug("Mahdollisessa FLASH-paivityksen ongelmatilanteessa, paivitystiedosto oli viallinen ja RM186 on epamaaraisessa tilassa.")
		LORAcom.UARTsyncLaird()
		# Kaynnistetaan radion ohjelmisto uudelleen
		resetRadioConnection();  # resetoidaan radiolaitteet
		debug("Init commands Lora.");
		LORAcom.LairdJoukoInit();
		if LoraMode or BTmode:
			LORAcom.LoraInit(); # liity verkkoon
			# alustaKommunikaatioLaite(); # kaynnistetaan kommunikaatiolaitteet
		if BTmode:
			alustaKommunikaatioSofta(); # kaynnistetaan kommunikaatiolaitteiden ohjelmistot


################# Kommunikaatio - viestien kasittely -funktioita #################################

def pakkaaViestidata(viesti):
	pakattuViesti="none";
	if "mittaukset" in viesti:
		debug("pakataan mittausviesti")
		pakattuViesti=viestinpurku.pakkaa_viesti("mittaukset", viesti); # viesti pakataan aina - GPRS ja LoRa
	if "laiteaika" in viesti:
		debug("pakataan synkronointiviesti")
		pakattuViesti=viestinpurku.pakkaa_viesti("aikasynk", viesti); # viesti pakataan aina - GPRS ja LoRa
	# if "viestityyppi in viesti: # if more messagetype --> add lines here - pakataan eri tavalla
		# TODO tahan lisaa viestityyppeja, jos niita tulee
	# ------ TODO release debug
	#debug("Viestidata on ennen pakkausta:" + str(viesti));
	#debug("Viestidata on pakkauksen jalkeen:" + str(pakattuViesti));
	
	if viestiPakataan==False:
		pakattuViesti=viesti;
	
	return pakattuViesti;

def puraViestidata(viestidata):
	purettuViestidata=viestidata;
	return purettuViestidata;

# -------------------viestien vastaanotto palvelimelta -----------------------------
def handleServerReply(replyMessage):
	debug("------------------------- saapuneen viestin kasittely alkaa ---------------------------------------------")
	palvelimenAikaSynkVastaus={} # tama funktio palauttaa erotuksen, jos laite synkronoidaan.
	debug("Kasitellaan purettua palvelimelta saapunutta viestia, jonka pitaisi olla DICT-objekti:")
	debug(replyMessage);
	if (not isinstance(replyMessage, dict)):
		debug("ERROR: Not a dict-object in handling server reply")
		return
		
	messageType=0
	global paivitaSofta;
				
	viestiTyyppi = next(iter(replyMessage)) # viestin tyyppi stringina # mita tama tekee? Ilmo
	debug("viestiTyyppi luettuna protobuf-viestista: " + viestiTyyppi);
	
	if viestiTyyppi==0: # viestiTyyppi==0: # ei tunnistettua viestia
		debug("Ei suoritettavaa palvelimelta.");
		return

	#if "viestityyppi_tahan_kohtaan" in replyMessage: # katkoo vain dict-objektin uloimman avaimen		
	if "aikasynk" in replyMessage:  # kasitellaan synkronointiviesti
		messageType=3; # test3=saatuData_str.find('aikasynk'); # {"aikasynk": {"erotus": 5}} - HUOM: erotus millisekunteina. TP-raspi
		
		aikasynk=replyMessage['aikasynk'] # koska DICT-objekti
		erotus=aikasynk['erotus'] # koska DICT-objekti
					
		debug ("Korjataan kelloa loopin loputtua erotuksen verran. Erotus on: " + str(erotus));
					
		integeritOK=False;
		try:
			erotus=int(erotus);
			if isinstance(erotus, int):
				integeritOK=True;
		except:
			debug("Ei ollut integeri.");
		
		if integeritOK:
			## Synkronoidaan vasta loopin jalkeen.
			# doTimeSynkDemo(erotus); # TODO - poista komennosta sana 'Demo', jolloin Raspi muuttaa omaa kelloaan 
			# doTimeSynk(erotus); # TODO - poista komennosta sana 'Demo', jolloin Raspi muuttaa omaa kelloaan --
			palvelimenAikaSynkVastaus={"erotus":erotus}
				
	if "katkot" in replyMessage:
		messageType=4; # test4=saatuData_str.find('katkot'); # {"katkot":[{"katkoID": 1, "laiteID": 2, "alku":1531531513, "loppu": 15315320}]}
		# sisaltaa katkoviestin
		debug("katkoAlkaa viesti saapunut. Kirjataan katko tietokantaan ja luodaan katkosaie, kun tarpeen.");
				
		katkoLista=[];
		katkoja=0;
		
		katkoLista=replyMessage['katkot'] # jos DICT-objekti
		#kaydaan lapi katkoObjektin sisaltama lista
		debug (katkoLista);
		katkoja=len(katkoLista);
		laskuri=0
		
		# katkoja voi olla useampia
		for i in range(0, katkoja):
			katkonAlkuun=-1;
			katkonKesto=-1;
			katkoTiedot=katkoLista[laskuri];
			laskuri=laskuri+1;
			try:
				katkoID=int(katkoTiedot['katkoID']);
				katkoLaiteID=int(katkoTiedot['laiteID']);
				katkonAlku=int(katkoTiedot['alku']);
				katkonLoppu=int(katkoTiedot['loppu']);
			except:
				debug("Ei ollut int-muotoisia.")
			kelloNyt = int(round(time.time()*1)) # timestamp in sec
			debug ("KelloNyt on :" + str(kelloNyt));
			katkonAlkuun = katkonAlku - kelloNyt;
			debug ("KatkonAlkuun  :" + str(katkonAlkuun));
			katkonKesto = katkonLoppu - katkonAlku;
			debug ("katkonKesto  :" + str(katkonKesto));
			# Check katkoDataOK;
			katkoDataOK=False;
			integeritOK=False;
					
			if isinstance(katkoID, int) and isinstance(katkoLaiteID, int) and isinstance(katkonAlku, int) and isinstance(katkonLoppu, int):
				integeritOK=True;
			if integeritOK:
				katkoDataOK=katkoSQL.checkKatkoDataOK(katkoID, katkoLaiteID, katkonAlkuun, katkonKesto);
			if katkoDataOK==True: #
				#debug("SQL -- Kirjataan tietokantaan: " + str(katkoID)+";"+str(katkoLaiteID)+";"+str(katkonAlku)+";"+str(katkonLoppu)+" - (katkoID;laiteID;alku;loppu)");
				# debug("Kirjataan SQL-tietokantaan: " + str(katkoID)+";"+str(katkoLaiteID)+";"+str(katkonAlku)+";"+str(katkonLoppu)+";False");
				katkoSQL.lisaaKatkotiedot(katkoID, katkoLaiteID, katkonAlku, katkonLoppu, False); # INSERT INTO Katkotiedot VALUES (katkoID, katkoLaiteID, katkonAlku, katkonLoppu, False) # SQL		
			katkoSQL.tarkastaKatkotaulu(); # SQL # luetaan tietokanta lapi ja tehdaan katkoille tarvittavat toimenpiteet # SQL
				
	if "katkonestot" in replyMessage:
		messageType=5; # test5=saatuData_str.find('katkonestot'); # {"katkonestot":[{"katkoID": 5}, {"katkoID": 8}]} 
		# katkoestetty

		debug("katkonesto viesti saapunut");
		katkonEstoLista=[];
		katkoja=0;
		debug("replyMessage: ");
		debug(replyMessage);
		katkonEstoLista=replyMessage['katkonestot'] # jos DICT-objekti
		debug ("katkonEstoLista: ");
		debug (katkonEstoLista);
		estoja=len(katkonEstoLista);
		debug ("estoja: " +str(estoja));

		laskuri=0;
		# katkoja voi olla useampia
		for i in range(0, estoja):
			integeritOK=False;
			katkoTiedot=katkonEstoLista[laskuri];
			debug("katkoTiedot:")
			debug(katkoTiedot)
			laskuri=laskuri+1;
			katkoID=katkoTiedot['katkoID'];
			debug("katkoID:")
			debug(katkoID)
			try:
				katkoID=int(katkoID)
				if isinstance(katkoID, int):
					integeritOK=True;
			except:
				debug("KatkoID ei ollut integer")
			if integeritOK:
				debug("Poistetaan tietokannasta:");
				debug("katkoID:" + str(katkoID));
				katkoSQL.poistaYksiKatkotieto(katkoID);
				pass;
				
		
	if "sbUpdateStart" in replyMessage:
		messageType=7; # test7=saatuData_str.find('sbUpdateStart'); # {"sbUpdateStart": {"numFiles": 35}}
		# paivitysalkaa
		
		debug("Paivitys alkaa viesti saapunut. TODO: Luodaan tyhja kansio ja varmistetaan sen olevan tyhja. ");
		tiedostojenLkm=0;
		# saatuData_obj=json.loads(replyMessage); # jos JSON
		# tiedostojenLkm=saatuData_obj['sbUpdateStart']['numFiles'];
		tiedostojenLkm=replyMessage['sbUpdateStart']['numFiles']
		debug ("tiedostojenLkm :" + str(tiedostojenLkm));
	
	if "sbUpdatePart" in replyMessage:
		messageType=8; # test8=saatuData_str.find('sbUpdatePart'); # {"sbUpdatePart": {"num": "0001", "part": "base64-dataa"}}
		# paivityspala saapui
		debug("Paivitys paketin pala saapunut. Tallennetaan.");
		# 8 {"sbUpdatePart": {"num": "0001", "part": "base64-dataa tai binaaria"}}
		paivitysPalaTiedot={};
		paivitysPalaData64="";
		paivitysPalaDataBinaryStr="";
		textStr="";
		tiedostonnimi="";
		paivitysPalaNum=0;
		
		paivitysPalaTiedot=replyMessage['sbUpdatePart'];
		paivitysPalaNum=paivitysPalaTiedot['num']
		paivitysPalaData64=paivitysPalaTiedot['part'];
		tiedostonnimi="part"+str(paivitysPalaNum);
		debug ("base64data: " + str(paivitysPalaData64));
		paivitysPalaDataBinaryStr=base64.b64decode(paivitysPalaData64);
		textStr=paivitysPalaDataBinaryStr.decode('utf-8')
		debug ("paivitysPalaData: " + str(textStr));
		overWriteData(tiedostonnimi,textStr);
		
		
	if "sbUpdateStop" in replyMessage:
		messageType=9; # test9=saatuData_str.find('sbUpdateStop'); #{"sbUpdateStop": {"splitSize": 128, "numFiles": 35}}
		# paivitys odottaa asentamista
		debug("paivitys loppuu viesti. Koostetaan tiedosto ja ajetaan paivitys.");
			
		tiedostojenLkm=0;
		testOK=True; # TODO Tarkastetaan etta paivityskansio on olemassa ja voidaan ajaa paivitys.
		if testOK:
			paivitysLoppuuTiedot=replyMessage['sbUpdateStop']; 
			splitSize=paivitysLoppuuTiedot['splitSize'];
			tiedostojenLkm=paivitysLoppuuTiedot['numFiles'];
			debug ("Koostetaan paivitys: "  + str(tiedostojenLkm) + " kpl, " + str(splitSize) +" byten tiedostoa ");
			partnum=0;
			# parts = os.listdir(source_dir) # Get a list of the file parts
			# parts.sort() # Sort them by name (remember that the order num is part of the file name)
			# laske lukumaara
			for i in range(0, tiedostojenLkm):
				debug("Check that files exist!");
				filename = os.path.join(splitFolder, 'part'+str(partnum).zfill(4))
				debug (filename);
				partnum += 1;
			join(splitFolder, joinedFile, splitSize);
			debug ("Join done to file: "+ joinedFile);
			debug ("Nostetaan paivitaSofta-bitti ylos ja paivitetaan seuraavan viestin lahetyksen jalkeen, jos ei ole katkoja tulossa.")
			paivitaSofta=True
			
	debug("Saapui viesti, joka kasiteltiin. Viestityyppi oli: "+str(messageType));
	return palvelimenAikaSynkVastaus;
	
	# 3 {"aikasynk": {"erotus": 5}} - HUOM: erotus millisekunteina. TP-raspi		
	# 4 {"katkot":[{"katkoID": 1, "laiteID": 2, "alku":531531513, "loppu": 5315320}]}
	# 5 {"katkonestot":[{"katkoID": 5}, {"katkoID": 8}]} 
	# 7 {"sbUpdateStart": {"numFiles": 35}}
	# 8 {"sbUpdatePart": {"num": "0001", "part": "base64-dataa"}}
	# 9 {"sbUpdateStop": {"splitSize": 128, "numFiles": 35}}
	
	#viestiTyyppi=3; # kelloajan synkronointiviesti
	#viestiTyyppi=4; # katkoAlkaa viesti
	#viestiTyyppi=5; # katkon esto viesti
	#viestiTyyppi=7; # paivitys alkaa viesti
	#viestiTyyppi=8; # paivitys saapuu viesti
	#viestiTyyppi=9; # paivitys loppuu viesti
	
	
#######################################################################################
# ------------------------------- SERVER COMM --------------------------------------- #
#######################################################################################


################################################################################################
# ------------------- kommunikaation funktioita -----------------------------
# TODO BT COMM # zzz
def sendToBT(viesti):
	sendingToBT="sending message to BT-device. Message: " + str(viesti);
	debug(sendingToBT);
	paluuViesti="PaluuViesti BT:n kautta";
	return paluuViesti;


def radioConnectionReady(): # TODO zzzz luo fiksut tarkastukset --> ja resetit
	debug("Kevyt tarkistus, etta laite vastaa kuten pitaakin.")
	kunnossa=False
	if GPRSMode:
		pass
		kunnossa=GPRScom.RadioTestOK();
		debug("Tarkastetaan IP-osoite tms.")
	if TurboMode:
		pass
		kunnossa=Turbocom.RadioTestOK();
		debug("Tarkastetaan IP-osoite tms.")
	if LoraMode:
		pass
		debug("Tarkastetaan RM186test ja DR komennolla get 2")
		reply=LORAcom.LoraRadioTestOK();
		if reply==True:
			kunnossa=True
	return kunnossa;
			

def resetRadioConnection(): # TODO zzzz luo fiksut resetit radioyhteydelle
	debug("Annetaan reset Radiolaitteelle.")
	if GPRSMode:
		reply=GPRScom.softReset()
		pass
	if TurboMode:
		reply=Turbocom.softReset()
		pass
	if LoraMode:
		reply=LORAcom.softReset()
		pass

def hardResetRadioDevice(): # TODO zzzz luo fiksut resetit radiolaitteen virran katkaisulle
	debug("Annetaan GPIOn kautta ohjaten fyysinen reset Radiolaitteelle.")
	if GPRSMode:
		GPIOhallinta.UART_to_SIMCOM();
		GPRScom.hardReset()
		pass
	if TurboMode:
		GPIOhallinta.UART_to_SIMCOM();
		Turbocom.hardReset()
	if LoraMode:
		GPIOhallinta.UART_to_LAIRD();
		LORAcom.hardReset()
		pass

def softResetRadioDevice(): # TODO zzzz luo fiksut resetit radiolaitteen virran katkaisulle
	debug("SortReset -- TODO loogiseksi - Annetaan GPIOn kautta ohjaten fyysinen reset Radiolaitteelle.")
	if GPRSMode:
		pass
		hardResetRadioDevice(); # toistaiseksi sama soft ja hard reset
	if TurboMode:
		pass
		hardResetRadioDevice(); # toistaiseksi sama soft ja hard reset
	if LoraMode:
		pass
		hardResetRadioDevice(); # toistaiseksi sama soft ja hard reset

def resetSelf():
	debug("Resetting Raspberry device.")
	debug("TODO zzz add reset command OR physical reset.")

def sendToServer(viesti): # olettaa etta yhteys on jo muodostettu
	debug("------------------------- palvelinkommunikaatio alkaa ---------------------------------------------")
	global sendFailedCountToday, sendFailedCountInRow, sendSucceedCountInRow
	
	errorState=False;
	paluuViesti="";
	pakattuViesti="";
	viestiPalvelimelle=""
	pakattuViesti=pakkaaViestidata(viesti) # viesti pakataan aina - GPRS ja LoRa
				
	if GPRSMode:
		# Yhteyden tila varmennetaan GPRScom funktiolla. Ei tarpeen tassa.
		sendingToGPRS="sending message to JoukoServer via GPRS. Message: " + str(pakattuViesti);
		debug(sendingToGPRS);
		paluuViesti=GPRScom.sendHTTPmessageWhenGPRSConnected(pakattuViesti);
		
		# TODO - tahan valiin voitaisiin tehda SHA256-autentikointi, jos GPRS-viesti. Nyt ei tarpeen, kun kaytossa SSL ja protobuf, seka basic-auth
		# autentikoituVastaus=SHAauth(vastaus)
		
		postViestiToimitettu=GPRScom.onkoPostViestiToimitettu(); # tarkistetaan meniko httpPost-perille, jotta voidaan osoittaa se LED-valolla
		if postViestiToimitettu:
			global vilkutetaanPunaistaLedia;
			vilkutetaanPunaistaLedia=True;
		
		pass;
	
	if TurboMode:
		# Yhteyden tila varmennetaan GPRScom funktiolla. Ei tarpeen tassa.
		sendingToGPRS="sending message to JoukoServer via GPRS. Message: " + str(pakattuViesti);
		debug(sendingToGPRS);
		paluuViesti=Turbocom.sendHTTPmessageWhenGPRSConnected(pakattuViesti);
		
		# TODO - tahan valiin voitaisiin tehda SHA256-autentikointi, jos GPRS-viesti. Nyt ei tarpeen, kun kaytossa SSL ja protobuf, seka basic-auth
		# autentikoituVastaus=SHAauth(vastaus)
		
		postViestiToimitettu=Turbocom.onkoPostViestiToimitettu(); # tarkistetaan meniko httpPost-perille, jotta voidaan osoittaa se LED-valolla
		if postViestiToimitettu:
			global vilkutetaanPunaistaLedia;
			vilkutetaanPunaistaLedia=True;
		
		pass;
		
	if LoraMode:
		# TODO check connection status - jotenkin - kysy laitetila? zzz
		debug("Lahetetaan viesti JoukoServerille via Lora. Message: " + str(pakattuViesti));
		paluuViesti=LORAcom.LoraSend(pakattuViesti);
		
	if True: # virheenhallinta
		if paluuViesti=="RX ERROR": # resetoidaan laite, mikali kommunikaatio jumittaa 3 kertaa perakkain eli luultavasti 30 minuuttia.
			sendFailedCountToday+=1;
			sendFailedCountInRow+=1; 
			if not radioConnectionReady():
				resetRadioConnection()
				
			sendSucceedCountInRow=0;
		else:
			sendFailedCountInRow=0;
			sendSucceedCountInRow+=1;
		
		if sendFailedCountInRow==2: # resetoidaan yhteys
			resetRadioConnection(); 
		if sendFailedCountInRow==3: 
			hardResetRadioDevice(); # resetoidaan laite, mikali kommunikaatio jumittaa 3 kertaa perakkain eli luultavasti 30 minuuttia.	
			sendFailedCountInRow=0;
		
		if sendFailedCountToday==10:
			resetSelf() # resetoidaan Raspi, jos liikaa kommunikaatio virheita
			
		if sendSucceedCountInRow>18: # jos 2 tuntia putkeen onnistuneita viesteja, niin nollataan isompi laskuri
			sendFailedCountToday=0;
			
	if PCMode:
		debug("Lahetetaan viesti JoukoServerille suoraan olemassa olevan internetyhteyden kautta. Message: " + str(pakattuViesti));
		paluuViesti,errorState=PCcom.sendHTTPpost(pakattuViesti);
		if errorState:
			print("Viesti ei mennyt perille. Errorcode: "+str(paluuViesti));
		
	if fakeMode: # viestia ei pakata
		debug("Send data to FAKE server.\n");
		global fakePaluuViestiTyyppi;
		global fakeReplyMode;
		# fakePaluuViestiTyyppi=4; # test setting
		time.sleep(0.01)
		
		if fakeReplyMode:
			debug("FakeSending viestiPalvelimelle: " + str(viestiPalvelimelle));
			pakattuViesti=pakkaaViestidata(viestiPalvelimelle);
			debug("FakeSending pakattu viesti: " + str(pakattuViesti));
			# arvotaan valmiiksi seuraava viestityyppi --> jos testiviesteja > 1
			#viestiTyyppi=3; # kelloajan synkronointiviesti
			#viestiTyyppi=4; # katkoAlkaa viesti
			#viestiTyyppi=5; # katkon esto viesti
			#viestiTyyppi=7; # paivitys alkaa viesti
			#viestiTyyppi=8; # paivitys saapuu viesti
			#viestiTyyppi=9; # paivitys loppuu viesti
			katkottavaLaiteID=5;
			paluuViesti=FAKEcom.fakeSendWithType(viestiPalvelimelle, fakePaluuViestiTyyppi,katkottavaLaiteID) # versio 2 - valitse itse paluuviesti
			
			fakePaluuViestiTyyppi=random.randint(3, 8); # arvotaan viesti # tai valitse: 3,4,5,7,8,9	
			time.sleep(0.01)
			debug('Palvelin vastasi puskurista: '+str(paluuViesti));
		else:
			paluuViesti=''
			
	return paluuViesti;


#######################################################################################
# -------------------------- TOP LEVEL COMM ----------------------------------------- #
#######################################################################################

def LoraInitAll(): # turha
	debug("Init commands Lora.");
	LORAcom.LairdJoukoInit();
	LORAcom.LoraInit(); # liity verkkoon

def BTInit():
	debug("Init commands BT.");
	debug("TODO alustetaan BT-laitteen radio esim. RM186 run VSP1")
	

def alustaKommunikaatioLaite():
	if GPRSMode:
		alustusOK=False;
		debug("GPRS-COMM-laite. Otetaan SIMCOM-laite kayttoon. ");
		while (not alustusOK) and (not GPRSJoinedAtStart):
			reply=GPRScom.alustaLaite()
			if "OK" in reply:
				debug("GPRS-laite alustettu onnistuneesti.")
				alustusOK=True;
			else:
				debug("Alustetaan laite uudelleen resetoinnin jalkeen.")
				GPRScom.hardReset();
				time.sleep(2)
	if TurboMode:
		alustusOK=False;
		debug("GPRS-COMM-laite. Otetaan SIMCOM-laite kayttoon. ");
		while (not alustusOK) and (not GPRSJoinedAtStart):
			reply=Turbocom.alustaLaite()
			if "OK" in reply:
				debug("GPRS-laite alustettu onnistuneesti.")
				alustusOK=True;
			else:
				debug("Alustetaan laite uudelleen resetoinnin jalkeen.")
				Turbocom.hardReset();
				time.sleep(2)
	
					
		# TODO onnistuiko: "OK", jos onnistui
	if LoraMode:
		debug("Lora-kommunikaatio kaytossa. Otetaan Laird-laite kayttoon. ");
		if (not LoraJoinedAtStart):
			LORAcom.LairdJoukoInit(); #alustaLora();
	if BTmode:
		debug("BT-kommunikaatio kaytossa eli BT-laite on taman GPRS-laitteen alaisuudessa. Luodaan BT-yhteydet.");
		# alustaBT();
		debug("Alusta BT");
	if fakeMode:
		debug("Alustetaan FAKE-kommunikaatiolaite")

def randomTaukoKatkonJalkeen(): 		
	if fakeTimeSpeedUp: ## TODO avaa lopulliseen versioon
		randomDelay=(random.randint(0, 1000))/1000; # arvotaan 1-3s delay 10 * 60 s = 600s
	else:
		# purskeidenLukemisVali = 30 s, mittausPurskeita = 10, mittauksiaTallennetaan = 2; # 2 x 10 x 30 = 600 s
		randomDelay=(random.randint(0, (mittauksiaTallennetaan*mittausPurskeita*purskeidenLukemisVali))); # arvotaan 0-10min delay 10 * 60 s = 600s 
		# TODO remove next line
		# randomDelay=(random.randint(1000, 2000))/1000; # arvotaan 1-3s delay 10 * 60 s = 600s
	debug("Laitteen uudelleen kaynnistys --> Random delay: " + str(randomDelay) + " s");
	if OhitaAlunTauko:
		debug("Ohitetaan alun tauko. TODO poista lopullisesta.")
		randomDelay=1;
	if randomDelay<0:
		randomDelay=0.001; # Varmistus muuttujan arvolle
	time.sleep(randomDelay);

def alustaKommunikaatioSofta():
	global vilkutetaanPunaistaLedia;
	if GPRSMode:
		debug("GPRS-COMM-laite. Otetaan GPRS-softa kayttoon. ");
		if (not GPRSJoinedAtStart):
			yhteysMuodostettu=False;
			seuraavaksiHardReset=False;
			while (not yhteysMuodostettu):
				debug("Muodostetaan GPRS-yhteys")
				time.sleep(1)
				yhteysMuodostettu=GPRScom.initGPRS(); #onnistuiko: "True", jos onnistui
				if (not yhteysMuodostettu):
					debug("Yhteyden muodostaminen ei onnistunut")
					time.sleep(1)
					if (not seuraavaksiHardReset):
						resetRadioConnection();
						seuraavaksiHardReset=True;
					else:
						resetRadioConnection();
						seuraavaksiHardReset=False
					time.sleep(1);
			debug("GPRS-yhteys muodostettu OK.")
			vilkutetaanPunaistaLedia=True; # vilkutetaan PUN LED
	if TurboMode:
		debug("GPRS-COMM-laite. Otetaan GPRS-softa kayttoon. ");
		if (not GPRSJoinedAtStart):
			yhteysMuodostettu=False;
			seuraavaksiHardReset=False;
			while (not yhteysMuodostettu):
				debug("Muodostetaan GPRS-yhteys")
				time.sleep(1)
				yhteysMuodostettu=Turbocom.initGPRS(); #onnistuiko: "True", jos onnistui
				if (not yhteysMuodostettu):
					debug("Yhteyden muodostaminen ei onnistunut")
					time.sleep(1)
					if (not seuraavaksiHardReset):
						resetRadioConnection();
						seuraavaksiHardReset=True;
					else:
						resetRadioConnection();
						seuraavaksiHardReset=False
					time.sleep(1);
			debug("GPRS-yhteys muodostettu OK.")
			vilkutetaanPunaistaLedia=True; # vilkutetaan PUN LED					
	if LoraMode:
		debug("Lora-kommunikaatio kaytossa. Otetaan Lora-Softa kayttoon. ");
		if (not LoraJoinedAtStart):
			reply=LORAcom.LoraInit(); #alustaLora();
	if BTmode:
		debug("BT-kommunikaatio kaytossa eli BT-laite on taman GPRS-laitteen alaisuudessa. Luodaan BT-yhteydet.");
		BTInit();
	if fakeMode:
		debug("Alustetaan FAKE-kommunikaatiolaitteen softa.")

# ------------------- MITTAUSTEN LUKEMINEN   -----------------------------
def lueReleTieto():
	if Raspi:
		releTieto=GPIOhallinta.lueReleTieto1();
	else:
		releTieto=mittausSimulaattori.lueReleTieto();
	# TODO pitaako muuttaa True-->1, False-->0 
	releTietoInt=booleanToInt(releTieto) # TODO kysy Ilmo, miten halutaan
	return releTietoInt; # 1=rele johtaa

#########################################################################################################


# -------------------viestit palvelimelle  -----------------------------

def sendTimeSynk():
	# {"aikasynk": {"laiteaika": 53153531}} - HUOM: millisekunteina; TP:n aika on kehyksessa millisekunteina
	aikaleimaNyt = int(round(time.time() * 1000));
	viesti = {"aikasynk": {"laiteaika": aikaleimaNyt}};
	paluuViesti=sendToServer(str(viesti));

def luoLyhytMittausviesti(kokoMittausviesti): # vanha - ei kayteta enaa - TODO remove
	global mittauksiaTallennetaan;
	keskiarvo1=0;
	keskiarvo2=0;
	keskiarvo3=0;
	kertyma1=0;
	kertyma2=0;
	kertyma3=0;
	for i in range (0, mittauksiaTallennetaan):
		mittausTemp=kokoMittausviesti["mittaukset"][i];
		vaihe1KA, vaihe2KA, vaihe3KA, releOhjaus = mittausTemp;
		kertyma1+=vaihe1KA;
		kertyma2+=vaihe2KA;
		kertyma3+=vaihe3KA;
	keskiarvo1=int(round(kertyma1/mittauksiaTallennetaan));
	keskiarvo2=int(round(kertyma2/mittauksiaTallennetaan));
	keskiarvo3=int(round(kertyma3/mittauksiaTallennetaan));
	tulosMittaukset = [(keskiarvo1, keskiarvo2, keskiarvo3, releOhjaus)];
	lyhytViesti={"mittaukset": tulosMittaukset, "pituusMinuutteina": kommunikaatioValinPituus};
		
	if viestiPakataan: # todo remove ehdollisuus lopullisesta
		pakattuLyhytViesti=viestinpurku.pakkaa_viesti({"mittaukset": tulosMittaukset, "pituusMinuutteina": kommunikaatioValinPituus});
		lyhytViesti=pakattuLyhytViesti
	## kommunikaatioValinPituus = mittauksiaTallennetaan * mittausJaksonPituus
	return lyhytViesti;


def luoLyhyetMittausviestit(kokoMittausviesti): # jaetaan koko viesti 2 osaan - TODO jaanee tarpeettomaksi syklimuutosten jalkeen
	mittaukset = kokoMittausviesti["mittaukset"]
	pituusMinuutteina = kokoMittausviesti.get("pituusMinuutteina", 5)
	mittaukset1 = mittaukset[:len(mittaukset)/2]
	mittaukset2 = mittaukset[len(mittaukset)/2:]
	aika1 = kokoMittausviesti["aika"] - pituusMinuutteina * len(mittaukset2) * 60
	aika2 = kokoMittausviesti["aika"]
	viesti1 = dict(kokoMittausviesti)
	viesti2 = dict(kokoMittausviesti)
	viesti1["mittaukset"] = mittaukset1
	viesti2["mittaukset"] = mittaukset2
	viesti1["aika"] = aika1
	viesti2["aika"] = aika2
	return (viesti1, viesti2)


def luoLyhyetMittausviestit3(kokoMittausviesti): # jaetaan koko viesti 3 osaan - TODO jaanee tarpeettomaksi syklimuutosten jalkeen
	mittaukset = kokoMittausviesti["mittaukset"]
	pituusMinuutteina = kokoMittausviesti.get("pituusMinuutteina", 5)
	mittaukset1 = mittaukset[:len(mittaukset)/3]
	mittaukset2 = mittaukset[len(mittaukset)/3:2*(len(mittaukset)/3)]
	mittaukset3 = mittaukset[2*(len(mittaukset)/3):]
	aika1 = kokoMittausviesti["aika"] - pituusMinuutteina * (len(mittaukset2) + len(mittaukset3)) * 60
	aika2 = kokoMittausviesti["aika"] - pituusMinuutteina * len(mittaukset3) * 60
	aika3 = kokoMittausviesti["aika"]
	viesti1 = dict(kokoMittausviesti)
	viesti2 = dict(kokoMittausviesti)
	viesti3 = dict(kokoMittausviesti)
	viesti1["mittaukset"] = mittaukset1
	viesti2["mittaukset"] = mittaukset2
	viesti3["mittaukset"] = mittaukset3
	viesti1["aika"] = aika1
	viesti2["aika"] = aika2
	viesti3["aika"] = aika3
	return (viesti1, viesti2, viesti3)

def loraSendToServerInThreeParts(kokoMittausViesti): # TODO jaanee tarpeettomaksi  - kommunikaationopeus pyritaan ennakoimaan
	LoraDataRate=2; # turha alustus
	if (LoraDataRate<3) and ("mittaukset" in kokoMittausViesti): # TODO testataan lyhyt viesti rakenne			
		# jaetaan viesti kolmeen palaan
		lyhytMittausviesti1,lyhytMittausviesti2,lyhytMittausviesti3=luoLyhyetMittausviestit3(kokoMittausViesti)
		debug("Lahetetaan lyhyet viestit JoukoServerille via Lora. Message1: " + str(lyhytMittausviesti1) + "Message2: " +str(lyhytMittausviesti2)+ "Message3: " +str(lyhytMittausviesti3));
		
		# eka viesti
		paluuViesti=sendToServer(lyhytMittausviesti1);
		paluuViestiDictPala=parseServerMessage(paluuViesti);
		if paluuViestiDictPala:
			palvelimenAikaSynkVastaus=handleServerReply(paluuViestiDictPala);
		if not paluuViestiDictPala:
			debug("Ei paluuviestia palvelimelta ekassa vastauksessa");
		
		# toka viesti
		time.sleep(10) # no sleep till Brooklyn
		paluuViesti=sendToServer(lyhytMittausviesti2);
		paluuViestiDictPala=parseServerMessage(paluuViesti);
		if paluuViestiDictPala:
			palvelimenAikaSynkVastaus=handleServerReply(paluuViestiDictPala);
		if not paluuViestiDictPala:
			debug("Ei paluuviestia palvelimelta ekassa vastauksessa");
		
		# kolmas viesti
		time.sleep(10) # no sleep till Brooklyn
		paluuViesti=sendToServer(lyhytMittausviesti3);
		paluuViestiDictPala=parseServerMessage(paluuViesti);
		if paluuViestiDictPala:
			palvelimenAikaSynkVastaus=handleServerReply(paluuViestiDictPala);
		if not paluuViestiDictPala:
			debug("Ei paluuviestia palvelimelta");
			
	
####################################################################################
# Mittauslooppi: 
# 5 minuutin mittausKierros (jossa 10 mittausta - 4 s mittausta ja 26 s taukoa)  
# mittausKierrostenKetju, jossa 2-6 mittausKierrosta eli (10-30min)
####################################################################################

def mittausKierros(mittausPurskeita=10): # 5 minuutin keskiarvon mittaaminen
	global mittauksiaLuettu;
	global liukuvaTeho1;
	global liukuvaTeho2;
	global liukuvaTeho3;
	global tallennuksia;
	
	mittauksiaLuettu=0;
	liukuvaTeho1=0;
	liukuvaTeho2=0;
	liukuvaTeho3=0;
	liukuvaMittauksetKestiMillisec=0;
	
	for j in range(0, mittausPurskeita): # 5 minuutin looppi eli mittausPurskeita = 10
		kaikkiOK=True;
		if LoraMode:
		   kaikkiOK=hallitseIntegrity()
		if (not kaikkiOK):
		   debug("On syyta epailla, etta Laird toimii virheellisesti.")

		mittaustenAlkuAika = int(round(time.time() * 1000)); # aikaleima millisekunteina
		mittauksiaLuettu +=1;
		
		# LED-vilkutus n. 3s alkaa # Asetetaan punainen LED pois paalta
		GPIOhallinta.LED3off();
		
		if simuloituMittaus:
			average1teho, average2teho, average3teho, mittausKestiMillisec = mittausSimulaattori.mittausLooppi(fakeTimeSpeedUp); # luetaan 3 x 1s tehot
		else:
			average1teho, average2teho, average3teho, mittausKestiMillisec = mittausMCP3008.mittausLooppi(); # luetaan 3 x 1s tehot
		
		# LED-vilkutus n. 3s loppuu # Asetetaan punainen LED takaisin paalle.
		GPIOhallinta.LED3on();
		
		#liukuvat keskiarvot
		liukuvaTeho1+=average1teho;
		liukuvaTeho2+=average2teho;
		liukuvaTeho3+=average3teho;
		liukuvaMittauksetKestiMillisec+=mittausKestiMillisec;
		debug ("Mittaus numero: " + str(mittauksiaLuettu)+" ; mittausKestiMillisec: " + str(mittausKestiMillisec)+" ms ; average1teho: " + str(average1teho)+" W ; liukuvaTeho1: " +str(liukuvaTeho1)+" W.");
		
		# eri kierroksilla tehdaan eri asioita: 
		  # eka kierros --> viedaan komento BT-laitteelle
		  # 2 - 8 # vapaana
		  # TODO luetaan jossain valissa pulsseja Lairdilta
		  # 9 eli toiseksi viimeinen kierros --> haetaan mittausdata BT-laitteelta
		  # 10 eli viimeinen kierros --> jatetaan tauko valiin, koska saatetaan lahettaa dataa palvelimelle
		
		if mittauksiaLuettu==1: # eka kierros  # ekalla kierroksella toimitetaan palvelimen viestit BT-laitteille
			debug("Mittauskierros - 1 mittaus luettu. --> Tarkastetaan katkotietokanta ja luodaan tarvittavat katkosäikeet.")
			katkoSQL.tarkastaKatkotaulu();
			global vilkutetaanPunaistaLedia;
			if vilkutetaanPunaistaLedia:
				GPIOhallinta.LED3vilkutus(vilkutuskertoja=20, vilkutusnopeus=0.5); # vilkutuskertoja=20, vilkutusnopeus=0.5)
				vilkutetaanPunaistaLedia=False;
			if BTmode:
				# debug("Eka mittauskierros. Lahetetaan BT-laitteen kaskyt, jos orjalaitteita.")
				debug("Ekalla kierroksella toimitetaan palvelimen viestit BT-laitteille")
				### TODO send(BT)
				nukutaan=random.randint(2, 8); # TODO remove 
				debug("BT-laitteiden kanssa jutellessa meni aikaa: " + str(nukutaan)+" s. TODO. Tee BT-com")
				if nukutaan<0:
					nukutaan=0.001; # Varmistus muuttujan arvolle
				time.sleep(nukutaan);
				####
				debug("Odotellaan viela loput 30 sekuntia taman BT:n IF-lausekkeen ulkopuolella.")
			pass;
			
		if mittauksiaLuettu==(mittausPurskeita-1): # toiseksi viimeisella tauolla haetaan BT-laitteen mittaukset # todo check counter
			# luetaan BT-laitteen tiedot viimeista edellisella mittauskierroksella
			if BTmode:
				debug("luetaan BT-laitteen tiedot - viimeista edellisella mittauskierroksella")
			pass;
		if mittauksiaLuettu==mittausPurskeita: # jatetaan viimeinen tauko valiin
			debug("Viimeinen mittauskierros: "+str(mittauksiaLuettu)+" --> tauko jaa valiin.  Poistutaan mittausKierroksesta.");
			# debug("Luettiin viimeinen mittaus 5 minsan keskiarvoon. Jatetaan tauko valiin.")
		if mittauksiaLuettu<mittausPurskeita: # jatetaan viimeinen tauko valiin
			mittaustenLoppuAika = int(round((time.time() * 1000)+syklinPituusKorjaus)); # aikaleima millisekunteina + arvioitu loopin vaihdon kesto
			mittaustenKesto = mittaustenLoppuAika - mittaustenAlkuAika; # ms
			# debug ("Mittauksia luettu :" +str(mittauksiaLuettu));
			mittausTauko=purskeidenLukemisVali-(mittaustenKesto/1000); # 30 sekuntia - mittauksiin kaytetty aika
			if fakeTimeSpeedUp:
				mittausTauko=0.001; # TODO poista - ei jaksa odottaa testivaiheessa
			debug("Nukutaan mittausTauko: "+str(mittausTauko) + " s. (oletus 26s.)")
			if mittausTauko <0:
				mittausTauko=0.001;
			time.sleep(mittausTauko);
		
	# 5 minuuttia on mitattu. Kirjataan arvo.
	keskiArvoTeho1=int(round(liukuvaTeho1/mittausPurskeita));
	keskiArvoTeho2=int(round(liukuvaTeho2/mittausPurskeita));
	keskiArvoTeho3=int(round(liukuvaTeho3/mittausPurskeita));
	# debug("ehditaan tehda jotain n. 25 s ajan")
	# debug("Valmista tuli. Laskettiin 5 min keskiarvo.");
	debug("Palautetaan 5 min keskiarvot: {0} W ; {1} W ; {2} W - mittaaminen kesti : {3} ms / {4} pursketta ".format(keskiArvoTeho1,keskiArvoTeho2,keskiArvoTeho3,liukuvaMittauksetKestiMillisec,mittausPurskeita));
	return (keskiArvoTeho1, keskiArvoTeho2, keskiArvoTeho3,liukuvaMittauksetKestiMillisec);
	
	
def mittausKierrostenKetju(omaLaiteID, mittauksiaTallennetaanInput, mittausPurskeita, mittausKierroksenKesto=300):
	# MITTAUSLOOPPI - uusi 12 x 5 min looppi
	global tallennuksia;
	liukuvaKetjuKestiMillisec=0;
	if saveData: #alustetaan CSV-rakenne
		mittausViestiObj={};
		mittausViesti="";		
		payloadCSV=""; #"v:1\n"+str(omaLaiteID)+"\n"; # alustetaan CSV
	tallennuksia=0;	
	mittauksetListana = []
	for i in range(0, mittauksiaTallennetaanInput): # tallennetaan 2-6 kpl # 2 kpl, kun 10 min sykli - 6 kpl,kun 30 min sykli
		tallennuksia+=1;
		aikaleimaNyt = int(round(time.time() * 1000)) # timestamp in millisec
		aikaleimaNytSekunteina=int(round(aikaleimaNyt/1000));
		# lasketaan 5 min tehokeskiarvot
		keskiArvoTeho1, keskiArvoTeho2, keskiArvoTeho3,liukuvaMittauksetKestiMillisec = mittausKierros(mittausPurskeita);
		releenAsento=lueReleTieto(); # True = rele johtaa
		aikaleimaMittauskierroksenLopussa = int(round(time.time() * 1000)) # timestamp in millisec
		aikaleimaMittauskierroksenLopussaSekunteina=int(round(aikaleimaMittauskierroksenLopussa/1000));
		mittauksetListana.append((keskiArvoTeho1, keskiArvoTeho2, keskiArvoTeho3, releenAsento))
			
		debug ("5 min ka teho: liukuvaTeho1/mittausPurskeita = " + str(keskiArvoTeho1));
		# OLD: mittauksetListana.append((omaLaiteID, aikaleimaNytSekunteina, keskiArvoTeho1, keskiArvoTeho2, keskiArvoTeho3, releenAsento))
		liukuvaKetjuKestiMillisec+=liukuvaMittauksetKestiMillisec; # ajastuksen apumuuttuja
		if saveData: # turha - tarpeen vain kehitysvaiheessa # TODO poista - turha 
			mittausTietoString=str(aikaleimaNytSekunteina) + "," +str(keskiArvoTeho1) + "," +str(keskiArvoTeho2) + "," +str(keskiArvoTeho3) + "," + str(releenAsento) + "\n";
			payloadCSVold=payloadCSV;  
			payloadCSV=payloadCSVold+mittausTietoString; 
			#kirjataan tiedostoon	
			pass
		aikaleimaLopussa = int(round(time.time() * 1000)) # timestamp in millisec
		debug("5 minuutin keskiarvoja on nyt kirjattu: " +str(tallennuksia)+" kpl. Keskiarvoja kirjataan, ennen lahettamista: "+str(mittauksiaTallennetaanInput)+" kpl.")
		KetjuKestiSec=(aikaleimaLopussa-aikaleimaNyt)/1000;
		debug("Koko 30min koko ketju kesti: " + str(KetjuKestiSec)+" s.")	
		if tallennuksia < mittauksiaTallennetaanInput: # tauko, jos turhaa aikaa mittausten valissa eika viimeinen mittaus	
			nukutaan=mittausKierroksenKesto-KetjuKestiSec; # 5 minuuttiin aikaa 5 * 60 = 300
			debug("---------------------- nukutaan mittausKierrostenKetjussa: " + str(nukutaan))
			if nukutaan>0:
				if fakeTimeSpeedUp:
					nukutaan=0.001; # TODO poista - ei jaksa odottaa testivaiheessa
					debug("Fake time SpeedUp --> nukutaan mittausKierrostenKetjussa: " + str(nukutaan))
				time.sleep(nukutaan)
			debug("Ketjun lopuksi nukuttiin: " + str(nukutaan)+" s.")
			pass
	
	if saveData:
		# debug ("payloadCSV: " + str(payloadCSV)); # TODO poista - turha 
		# 1. varmistetaan että vapaa 2. lukitaan "meas_lock" . 3. varmistetaan että vapaa 4. kirjoitetaan 5. avataan.
		writeData("datafile.csv",payloadCSV);	
		
	if fakeTimeSpeedUp: # fake loopin loppuaika
		global fakeStarttiAika;
		global fakeKierrosLaskuri;
		global kommunikaatioValinPituus;
				
		fakeKierrosLaskuri+=1;
		aikaleimaMittauskierroksenLopussaSekunteina=fakeStarttiAika+(fakeKierrosLaskuri*300*mittauksiaTallennetaanInput); # kierroskesto
		printtaaAikaleima(aikaleimaMittauskierroksenLopussaSekunteina);
	
	kokoMittausViesti={}
	kokoMittausViesti["mittaukset"]= mittauksetListana	
	kokoMittausViesti["laiteID"] = omaLaiteID
	kokoMittausViesti["aika"] = aikaleimaMittauskierroksenLopussaSekunteina; # oli ennen aikaleimaNytSekunteina - eli mittauskierroksen alku. TODO? kumpi?
	#kokoMittausViesti["pituusMinuutteina"] = 5;
	
	
	
	debug("Ketjun mittauksien toteuttaminen kesti: " + str(liukuvaKetjuKestiMillisec)+" ms.")
	print("Luotiin palvelimelle lahetettava viesti: {}".format(kokoMittausViesti))
	
	return (kokoMittausViesti, liukuvaKetjuKestiMillisec);

	
####################################################################################
# real COM - looppi
####################################################################################
def kommunikaatioLooppi(omaLaiteID):
	debug("------------------------- kommunikaatiolooppi alkaa ---------------------------------------------")
	loopinAlkuAika = int(round(time.time() * 1000)); # aikaleima millisekunteina
	
	global paivitaSofta; # True, jos on ladattu asennettavaksi uusi smartBasic-ohjelma
			
	global mittauksiaTallennetaan;
	global odoteltuLiikaaAiemmin;
	# tahan valiin tulee 10 minuutin valein tehtavat tarkastukset tms.
	lyhytMittausviesti="null"
	paluuViestiDictPala={};
		
	if LoraMode: # testataan DataRate ennen looppia ja maaritellaan loopin kesto
		LoraDataRate=LORAcom.LoraGetDataRate(); #tarkastetaan data rate eli kaytossa oleva Spreading Factor # komennolla: "lora get 2" 
		# Jos 0-2: max payload = 51 	
		# Jos 3: max payload = 115 
		# Jos 4-7: max payload = 222
		if LoraDataRate<3:
			mittauksiaTallennetaan=2; # 2 x 5 minuutin mittauskierros eli tallennetaan 2 keskiarvoa ja sitten sendToServer
		else:
			# LoraDataRate>=3
			mittauksiaTallennetaan=6; # 2 x 5 minuutin mittauskierros ja sendToServer
	
	kokoMittausViesti, liukuvaKetjuKestiMillisec=mittausKierrostenKetju(omaLaiteID, mittauksiaTallennetaan, mittausPurskeita, mittausKierroksenKestoSekunteina); # mittausviesti on luotu
	# debug("Kommunikaatiolooppi sending to server") # lahetetaan mittausviesti palvelimelle
	# kaikissa moodeissa yhteiset toiminnot 
	
	paluuViesti=sendToServer(kokoMittausViesti); # viesti lahetettiin palvelimelle ja saatiin paluuviesti
						
	paluuViestiDictPala=parseServerMessage(paluuViesti);  # kasitellaan paluuviesti palvelimelta		
	palvelimenAikaSynkVastaus={}
	if paluuViestiDictPala:
		palvelimenAikaSynkVastaus=handleServerReply(paluuViestiDictPala);
	if not paluuViestiDictPala:
		debug("Ei paluuviestia palvelimelta");
	
	# yksi mittaus/palvelin-sykli on suoritettu. Odotellaan ehka hetki.
	if paivitaSofta: # Asennetaan päivitys, jos on kokonaisuudessaan ladattu asennettavaksi uusi ehjä smartBasic-ohjelma.
		updateSmartBasic();
			
	################## Loopin kesto kiinnittaminen tasan 10 tai 30 minuuttiin ##########################
	loopinLoppuAika = int(round(time.time() * 1000)); # aikaleima millisekunteina
	loopinKesto = loopinLoppuAika - loopinAlkuAika; # aika millisekunteina - po noin 10 tai 30 min eli mittauksiaTallennetaan * 5 min
	debug("Loopin kesto oli: " +str(loopinKesto/1000) + " sekuntia. ") 
	
	if fakeTimeSpeedUp: # huijataan, etta looppi kesti halutun ajan
		loopinKesto=((mittauksiaTallennetaan*300)-0.001)*1000;	
		debug("Huijattu loopin kesto: " +str(loopinKesto/1000) + " sekuntia. ")  	
		
	looppiOliLiianNopea = (mittauksiaTallennetaan * mittausKierroksenKestoMinuutteina *60*1000) - (loopinKesto); # ms
	debug("------------------------------------------------------------------------- Odotellaan, etta : " +str(mittauksiaTallennetaan*mittausKierroksenKestoMinuutteina)+ " : minuuttia (oletus 10 tai 30) tulee tayteen eli odotetaan: " + str(looppiOliLiianNopea/1000) + " s")
	
	if odoteltuLiikaaAiemmin>300: # jos yli 5 minsaa jaljessa poistetaan kokonaiset 5 minuutin jaksot, joita ei saada kirittya kiinni
		# odoteltuLiikaaAiemmin=odoteltuLiikaaAiemmin-300; # TODO muutetaan jakojaannokseksi odoteltuLiikaaAiemmin MODULO 300
		odoteltuLiikaaAiemmin=odoteltuLiikaaAiemmin%300; # odoteltuLiikaaAiemmin MODULO 300
	seuraavaanLooppiinAikaa = looppiOliLiianNopea - odoteltuLiikaaAiemmin 
	
	if seuraavaanLooppiinAikaa>0:
		time.sleep(seuraavaanLooppiinAikaa/1000);
		odoteltuLiikaaAiemmin=0;
	else:
		odoteltuLiikaaAiemmin=0-(seuraavaanLooppiinAikaa/1000); # s
	debug("Paaloopin ajastuksen lopputasaus. Looppi oli liian nopea: "+str(looppiOliLiianNopea)+" ms ; Odoteltiin hetki: "+str(seuraavaanLooppiinAikaa) + " ms ; odoteltuLiikaaAiemmin: " + str(odoteltuLiikaaAiemmin))
	debug("Loopin loputtua aikasynk. Muuten tahdistus menee pieleen.")
	if "erotus" in palvelimenAikaSynkVastaus:
		erotus=palvelimenAikaSynkVastaus['erotus'];
		doTimeSynk(erotus); # Raspi muuttaa omaa kelloaan # TODO - kommentoi, niin aikasynk poistetaan kaytosta.
		# doTimeSynkDemo(erotus); # TODO - poista komennosta sana 'Demo', jolloin Raspi muuttaa omaa kelloaan

def orjaLaitteenKommunikaatioLooppi(omaLaiteID):
	# TODO - Tahan voidaan laatia BT-slave-laitteen looginen toiminta
	
	debug("------------------------- orjalaitteen - mittaus ja kommunikaatiolooppi alkaa ---------------------------------------------")
	loopinAlkuAika = int(round(time.time() * 1000)); # aikaleima millisekunteina
		
	global mittauksiaTallennetaan;
	global odoteltuLiikaaAiemmin;
	# tahan valiin tulee 10 minuutin valein tehtavat tarkastukset tms.
	lyhytMittausviesti="null"
	paluuViestiDictPala={};
	
	kokoMittausViesti, liukuvaKetjuKestiMillisec=mittausKierrostenKetju(omaLaiteID, mittauksiaTallennetaan, mittausPurskeita, mittausKierroksenKestoSekunteina); # mittausviesti on luotu
	# debug("Kommunikaatiolooppi sending to server") # lahetetaan mittausviesti palvelimelle
	# kaikissa moodeissa yhteiset toiminnot 
	
	paluuViesti=sendToServer(kokoMittausViesti); # viesti lahetettiin palvelimelle ja saatiin paluuviesti
						
	paluuViestiDictPala=parseServerMessage(paluuViesti);  # kasitellaan paluuviesti palvelimelta		
	
	palvelimenAikaSynkVastaus={}
	if paluuViestiDictPala:
		palvelimenAikaSynkVastaus=handleServerReply(paluuViestiDictPala);
	if not paluuViestiDictPala:
		debug("Ei paluuviestia palvelimelta");
	
	# yksi mittaus/palvelin-sykli on suoritettu. Odotellaan ehka hetki.
			
	################## Loopin kesto kiinnittaminen tasan 10 tai 30 minuuttiin ##########################
	loopinLoppuAika = int(round(time.time() * 1000)); # aikaleima millisekunteina
	loopinKesto = loopinLoppuAika - loopinAlkuAika; # aika millisekunteina - po noin 10 tai 30 min eli mittauksiaTallennetaan * 5 min
	debug("Loopin kesto oli: " +str(loopinKesto/1000) + " sekuntia. ") 
	
	if fakeTimeSpeedUp: # huijataan, etta looppi kesti halutun ajan
		loopinKesto=((mittauksiaTallennetaan*300)-0.001)*1000;	
		debug("Huijattu loopin kesto: " +str(loopinKesto/1000) + " sekuntia. ")  	
		
	looppiOliLiianNopea = (mittauksiaTallennetaan * mittausKierroksenKestoMinuutteina *60*1000) - (loopinKesto); # ms
	debug("------------------------------------------------------------------------- Odotellaan, etta : " +str(mittauksiaTallennetaan*5)+ " : minuuttia (oletus 10 tai 30) tulee tayteen eli odotetaan: " + str(looppiOliLiianNopea/1000) + " s")
	
	if odoteltuLiikaaAiemmin>300: # jos yli 5 minsaa jaljessa poistetaan kokonaiset 5 minuutin jaksot, joita ei saada kirittya kiinni
		# odoteltuLiikaaAiemmin=odoteltuLiikaaAiemmin-300; # TODO muutetaan jakojaannokseksi odoteltuLiikaaAiemmin MODULO 300
		odoteltuLiikaaAiemmin=odoteltuLiikaaAiemmin%300; # odoteltuLiikaaAiemmin MODULO 300
	seuraavaanLooppiinAikaa = looppiOliLiianNopea - odoteltuLiikaaAiemmin 
	
	if seuraavaanLooppiinAikaa>0:
		time.sleep(seuraavaanLooppiinAikaa/1000);
		odoteltuLiikaaAiemmin=0;
	else:
		odoteltuLiikaaAiemmin=0-(seuraavaanLooppiinAikaa/1000); # s
	debug("Paaloopin ajastuksen lopputasaus. Looppi oli liian nopea: "+str(looppiOliLiianNopea)+" ms ; Odoteltiin hetki: "+str(seuraavaanLooppiinAikaa) + " ms ; odoteltuLiikaaAiemmin: " + str(odoteltuLiikaaAiemmin))
	debug("Loopin loputtua aikasynk. Muuten tahdistus menee pieleen.")
	if "erotus" in palvelimenAikaSynkVastaus:
		erotus=palvelimenAikaSynkVastaus['erotus'];
		# doTimeSynk(erotus); # Raspi muuttaa omaa kelloaan
		doTimeSynkDemo(erotus); # TODO - poista komennosta sana 'Demo', jolloin Raspi muuttaa omaa kelloaan
			
		
def startRaspiProsedure():	
	debug('Clearing data files\n')
	clearDataFile("datafile.csv")
	# debug('setting Start delay as minimun - remove later')
	# poistetaan lukot BT-versiossa

def closeRaspiProsedure():
	debug("Suljetaan ohjelma, jota ennen vapautetaan IO ja suljetaan tietokanta")
	# Vapautetaan IO
	if Raspi:
		GPIOhallinta.vapautaIO();
	# vapautetaan SQL-tietokanta
	katkoSQL.suljeTietokanta();
	
#######################################################################################
# ------------------------------- MAIN alustukset ----------------------------------- #
#######################################################################################

startRaspiProsedure(); # Tarkistetaan asetukset ja tiedostot, alustetaan mittauslaitteisto yms.

if Raspi:
	GPIOhallinta.alustaIO(); # Alustetaan IO

# alustetaan tietokanta
katkoSQL.avaaTietokanta(); # avaa tietokanta ja luo jos puuttuu
katkoSQL.luoKatkotaulu();  # luo katkotaulu, jos puuttuu


################################################################################################################################
################################################################################################################################
kalibrointimittaukset=False;  # True
if kalibrointimittaukset:
	debug("Ajetaan kalibrointimittaukset")
	mittauksiaSekunninVerran=mittauksiaSekunnissa
	Raspi3=False;
	if Raspi3:
		mittauksiaSekunninVerran=mittauksiaSekunnissa*9;
	
	# Nollavirran kalibrointimittaus 
	# tiedostoon nollavirranraakamittaukset.csv tallennetaan mittausten tiedot: mittaussyklin nro; mittausten lukumaara; vaiheen1 virta-mittausten keskiarvo, vaiheen2 virta-mittausten keskiarvo, vaiheen3 virta-mittausten keskiarvo, mittausjakson kesto
	mittausMCP3008.nollavirranKalibrointimittaus(5, 3*mittauksiaSekunninVerran); # (keskiarvojaKirjataan=5,mittauksiaKalibroinnissa=1830)
	
	# Jannitteen kalibrointimittaus
	# tiedostoon janniteraakamittaukset.csv tallennetaan mittausten tiedot: mittaussyklin nro; mittausten lukumaara; mittausten keskiarvo
	mittausMCP3008.jannitemittausKalibrointiTiedostoon(5, 3*mittauksiaSekunninVerran); # (keskiarvojaKirjataan=5, mittauksiaKeskiarvoon=1830) 

ikuistetKalibrointimittaukset=False; # kalibroidaan niin kauan kuin virtaa riittaa
while ikuistetKalibrointimittaukset:
	debug("Ajetaan IKUISET kalibrointimittaukset")
	mittauksiaSekunninVerran=mittauksiaSekunnissa;
	Raspi3=False;
	if Raspi3:
		mittauksiaSekunninVerran=mittauksiaSekunnissa*9;
	mittausMCP3008.nollavirranKalibrointimittaus(5, mittauksiaSekunninVerran); # (keskiarvojaKirjataan=5,mittauksiaKalibroinnissa=1830)
	mittausMCP3008.jannitemittausKalibrointiTiedostoon(5, 3*mittauksiaSekunninVerran); # (keskiarvojaKirjataan=5, mittauksiaKeskiarvoon=1830) 

IOtestit=False; # Tassa valissa voi ajaa testeja: # TODO poistetaan lopullisesta
if IOtestit:
	debug("Ajetaan IO-testit")
	mittauksiaSekunninVerran=mittauksiaSekunnissa
	Raspi3=False;
	if Raspi3:
		mittauksiaSekunninVerran=mittauksiaSekunnissa*9;
	import IOtestit;
	debug("Ajetaan IO-testit")
	time.sleep(1)
	IOtestit.releidenTestaus(); # Avataan ja suljetaan 3 relettä sekunnin välein"

	# skaalaamattomat mittaukset
	debug("-------------------------- Skaalaamattomat mittaukset ---------------------");
		
	# Jannite
	IOtestit.LED3vilkutus(1, 1)# (vilkutuskertoja=1, vilkutusnopeus=1)
	IOtestit.jannitemittausTestiRajattu(2, mittauksiaSekunninVerran); # (kierroksia=5, mittauksiaKierroksella=100), 
	# Jannitteen kalibrointimittaus
	#mittausMCP3008.jannitemittausKalibrointiTiedostoon(10*mittauksiaSekunninVerran,5); # (mittauksiaKeskiarvoon=1830,keskiarvojaKirjataan=5)
		
	# Virrat
	IOtestit.raakaMittausTesti(5); # 10 mittauskertaa: virrat, AC, regu (yksittaisia mittauksia)
	IOtestit.LED3vilkutus(2,0.5)# (vilkutuskertoja=1, vilkutusnopeus=1) # debug("LED hidas vilkutus: 6 x 0.5 s (x2)")
	IOtestit.mittausTestiRajattu(2, mittauksiaSekunninVerran); # looppien lukumaara - tuloksia näytetään , # mittauksia yhteen keskiarvoon
	IOtestit.LED3vilkutus(1,0.3)# (vilkutuskertoja=1, vilkutusnopeus=1)
	IOtestit.ajetaanRaakaMittausKierros(3, mittauksiaSekunninVerran); #(kierroksia, mittauksiaPurskeessa)
	# skaalattu Tehomittaus
	
	debug("-------------------------- Skaalatut mittaukset ---------------------");
	IOtestit.LED3vilkutus(2, 2)# (vilkutuskertoja=1, vilkutusnopeus=1)
	time.sleep(1)
	IOtestit.tehomittausTestiRajattu(4); # 3 sekunnin kierroksia - oikealla mittausloopilla

	# "LOPETTAVAT" IOtestit
	# IOtestit.raakaMittausTestiLoputon()
	# IOtestit.selfResetTesti(); # sammutetaan raspi
	# IOtestit.mittausTesti(); # Mitataan tehoja oikealla mittausloopilla
	pass;
	if False:
		IOtestit.LED3vilkutus(2,0.5);
		closeRaspiProsedure()
		import sys;
		sys.exit();
		
		
UARTtesti=False;
if UARTtesti:
	import IOtestit;
	debug("Ajetaan UART-testi - main 1423")
	IOtestit.UARTtestiLora()
	
UARTtesti2=False;
if UARTtesti2:
	import IOtestit;	
	alustetaanko=False;
	IOtestit.LoraUARTtest(alustetaanko)
	# palautetaan alkuarvot ennen sykleja	
	# GPIOhallinta.resetoiIOalkuarvoihin();




################################################################################################################################
################################################################################################################################

# INIT
if Raspi:
	alustaKommunikaatioLaite() # Otetaan laite fyysisesti kayttoon ja valmistellaan softa - ei luoda yhteytta ulkomaailmaan
	randomTaukoKatkonJalkeen(); # random delay 0-10 min tai 0-30 min
	alustaKommunikaatioSofta(); # Alustetaan kommunikaatio, luodaan yhteys.

# Tarkistetaan laitteen looginen toiminta

###############################################################################
# ----------------------- MAIN LOOPPI -----------------------------------------
###############################################################################

# Jos kyseessa on BT-orjalaite, niin taysin oma looppi ajoon.
if BTslaveMode:
	debug("BT-orjalaitteen oma looppi alkaa.")
	while True:
		# TODO - tahan voidaan ohjelmoida BT-orjalaitteen toiminta
		orjaLaitteenKommunikaatioLooppi(omaLaiteID)

looppiLaskuri=0
if ikuisuusRajoitettu:
	for j in range(0, ikuisuudenRajoitettuKesto): # oli if True: # TODO muuta WHILE lopulliseen
		debug("Yksi pitka looppi suoritettu. Tahan valiin voidaan tehda esim. vuorokauden suoritettavat tarkastukset.")
		pass;
		for i in range(0, kommunikaatioLooppiKierroksia): # TODO tahan tulee while TAI sitten kutsuvaan looppiin while
			looppiLaskuri+=1
			kommunikaatioLooppi(omaLaiteID); # ------------- Ajetaan mittaus/palvelin-sykli - MITTAUSLOOPPI - 12 x 5 min
			# tahan valiin tulee vuorokauden valein tehtavat tarkastukset tms.
			debug("------------------------------- Yksi mittaus-palvelinsykli suoritettu. Kommunikaatioloopin mittaussyklikierroksia suoritettu: "+str(looppiLaskuri)+" kpl. Kierroksia suoritetaan yhteensa: "+str(kommunikaatioLooppiKierroksia)+" kpl.");
	pass;
	debug("------------------------------------ MAIN looppi komentaa. --------- KommunikaatioLooppeja suoritettu suoritettu: "+str(j+1)+"kpl / " + str(ikuisuudenRajoitettuKesto) + " kpl. Only a test setting. --> WHILE-loopiksi.");

else: # ajetaan looppia ikuisesti
	while True:
		kommunikaatioLooppi(omaLaiteID); # ------------- Ajetaan mittaus/palvelin-sykli - MITTAUSLOOPPI - 12 x 5 min
		# tahan valiin tulee vuorokauden valein tehtavat tarkastukset tms.
		pass;

# testivaiheessa lopetus;
if ikuisuusRajoitettu:
	closeRaspiProsedure()
	
