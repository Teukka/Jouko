#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################

# main_loop.py – main program
# - Main program, which starts automatically when the device starts up. This main program manages the measurement, break management and communications. This program calls other program components depending on how the functionality of the device is specified in json files (see descriptions of JSON files, eg settings in ‘asetukset.json’)
# - The program is executed as different alternating sequences, as the functions are not desired to run in parallel. In this way, the optimum state of the measurement is achieved with a limited processor power while the measurement process is not performed simultaneously with other functions. The result is consistent and high-quality measurement as well as the highest possible sampling rate as the measurement process always uses all possible processor power.
# main_loop.py – paaohjelma
# - Paaohjelmalooppi, joka kaynnistyy aina automaattisesti, kun laite kaynnistyy. Tama paaohjelma hallinnoi mittauksen, katkojen hallinnan ja kommunikaation vuorottelevan kokonaisuuden. Tama ohjelma kutsuu muita ohjelmakomponentteja riippuen siita, miten laitteen toiminnallisuus on json-tiedostoissa maaritelty (ks. JSON-tiedostojen kuvaukset, esim. asetukset.json)
# - Ohjelma suoritetaan erilaisina vuorottelevina sekvensseina, silla toimintoja ei haluta ajaa rinnakkaisesti. Nain saavutetaan erityisesti mittauksen kannalta optimaalinen tilanne rajallisella prosessoriteholla, kun mittausprosessin kanssa ei suoriteta yhtaaikaisesti muita toimintoja. Lopputuloksena on laadukas ja tasalaatuinen mittaustulos seka mahdollisimman suuri naytteenottotaajuus, kun mittausprosessi kayttaa aina kaiken mahdollisen prosessoritehon.

###################### Laitteelta serverille: ##############################
# Aikaleimat (paitsi aikasynk) sekunteina unix-eepokista, UTC-aikaa.
############################################################################

################################## Tarpeelliset Import ##########################################
import time;
import json;
import datetime;
import os;

try: # varmistetaan yhteensopivuus Python2 ja Python3
	import queue # Integrity
except ImportError:
	import Queue as queue; # import-komento riippuu Python-versiosta, koska eri nimi Python-versioissa

#import sqlite3; # tuodaan katkoSQL.py
#import threading; # tuodaan katkoSQL.py
#import math; # sqrt # tuodaan mittausMCP3008.py
#import re; # tuodaan viestinpurku.py

import random; # tarvitaan kaynnistykseen satunnainen viive - sahkokatkojen takia 	
import hmac;
import hashlib;
import base64;
import binascii;
import viestinpurku; #jossa import laiteviestit_pb2
import katkoSQL; # katkojen hallinta ja SQL-tietokanta

# Ladataan asetukset JSON-tiedostoista
# Asetukset jaettu useisiin eri tiedostoihin, jotta paivittaminen voidaan rajoittaa/sallia haluttuihin ominaisuuksiin:
# 1 - asetukset.json - yleiset asetukset kaikille laitteille: mittaussyklien ja kommunikaatiosyklien kestot, laitteen mittausnopeuden maaritteleminen
# 2 - kommunikaatio.json - kommunikaatio asetukset radioliikenteelle: # maaritellaan kommunikaatiokanava (GRPS, Lora tai ethernet) ja seka asetukset, kuten osoitteet, laitteiden nimet ja avaimet
# 3 - testiasetukset.json - kehitysvaiheessa hyodylliset testiasetukset. Voidaan helposti ottaa kayttoon ja poistaa kaytosta mm. testauksen nopeuttaminen taukoja lyhentamalla.
# 4 - kalibrointi.json – laitteistolle  kalibroidut arvot mittaustarkkuuden varmistamiseksi. Myos automaattinen virtamittauksen nollatason kalibrointi tallentaa arvonsa tanne. Automaattinen nollavirran kalibrointi, voidaan asettaa taalla paalle tai pois.
# 5 - paivityksenTila.json – maaritellaan paivityksen asetukset ja nykyisen ohjelmistopaivityksen versionumero
# Lisaksi tiedostoissa on mm.
# 6 - toimintatila.json – valitaan laitteen toimintatila kalibrointimittauksia varten: kalibroidaanJannite, kalibroidaanVirta, ja varmennetaanKalibrointi.
# 7 - ohjelmanTila.json – kaytetaan kertomaan laitteiston oikeellisesta toiminnasta.


with open('asetukset.json') as json_general_settings_file:
	asetus	= json.load(json_general_settings_file)
with open('kommunikaatio.json') as json_com_settings_file:
	kommunikaatioasetus	= json.load(json_com_settings_file)
with open('testiasetukset.json') as json_testi_settings_file:
	testiasetus	= json.load(json_testi_settings_file)
with open('kalibrointi.json') as json_kalibrointi_settings_file:
	kalibrointiasetus = json.load(json_kalibrointi_settings_file)
with open('paivityksenTila.json') as json_paivitys_settings_file:
	paivitysasetus = json.load(json_paivitys_settings_file)

# ladattuihin muuttujiin viitataan:
# kommunikaatioasetus['com']['muuttujan_nimi'] , kun kommunikaatio-asetukset
# kommunikaatioasetus['GPRS']['muuttujan_nimi'] , kun GPRS-kommunikaatio-asetukset
# asetus['general']['muuttujan_nimi'] , kun yleiset asetukset
# testiasetus['test']['muuttujan_nimi'] , kun testi-asetukset

debugON=testiasetus['test']['debugON'];# True; # kun 1, niin ei nayteta debug-funktion viesteja

def debug(data): # Komento, jolla annetaan palautetta johonkin kanavaan. Nyt tulostetaan data terminaaliin. Voidaan asettaa keskitetysti pois paalta.
	if debugON:
		print (str(data));

#### Heti alussa kaynnistetaan jarjestelman kuntoa valvovat ohjelmat. 
lokitiedosto="nohup.out";
open(lokitiedosto, 'w').close() # poistetaan aiempi valvoja saikeen loki
pid=os.fork()
if pid==0:
	os.system("nohup python ./valvoja.py &")
	exit()

#### KOMMUNIKAATIOASETUSTEN ALUSTAMINEN ############################################################################################################################## -- ##
# -------------------- Laiteversion konffaus -----------------------
GPRSMode = kommunikaatioasetus['com']['GPRSMode']; # True; # 1, jos GPRS-COMM-laite
LoraMode = kommunikaatioasetus['com']['LoraMode']; # False; # 1, jos Lora-laite
BTmode = kommunikaatioasetus['com']['BTmode'];		# True, jos BT-laite GPRS:n alaisuudessa # eli BT Central-laite

ethernetMode = kommunikaatioasetus['com']['ethernetMode'];		# True, jos kaytetaan laitteeseen valmiiksi luotua ethernet-yhteyttaa

# Kytkin-laite, jossa vain BT-radio eli BT Peripheral-laite:
BTslaveMode = kommunikaatioasetus['com']['BTslaveMode'];	# True, jos tama on BT-orjalaite. Huom! erilainen looginen toiminta ja taysin oma paalooppi 

# --------------------------------------- AJASTUKSET ---------------------------# luetaan asetukset tiedostosta
purskeidenLukemisVali=asetus['general']['purskeidenLukemisVali']; # 30 ; # 30 s Mittaustiheys ka. varten #
mittausPurskeita=asetus['general']['mittausPurskeita'];# 10 kpl 30 sekunnin mittauksia 5 minuutin keskiarvoon
global mittauksiaTallennetaan; # HUOM TASSA alustetaan GPRS-syklin pituus (oletus: n x 5 min)
mittauksiaTallennetaan=asetus['general']['mittauksiaTallennetaan'];# 6 kpl 5 minuutin keskiarvoja tallennetaan ennen muuta toiminta # TAI 2 kpl jos 10 min sykli 
mittauksiaSekunnissa=asetus['general']['mittauksiaSekunnissa'];# 1596; # 183 Laiteriippuvainen eli monta mittausta ehtii lukea sekunnissa

syklinPituusKorjaus=67; # 67=114-47 (12.10.2018) ; #114=147-33 #147=490-343  liukuma 0.343/purske - 490; # 6 vrk-syklin tulos: viive 0,439626 490ms=50ms+440ms # Kalibroitu viive 2vrk mittauksilla 26.9.2018 # 50 ms Oletetaan kuinka paljon aikaa kuluu, kun ajastus ei ole kaynnissa (eli syklin ulkopuolella - vanhasta uuteen sykliin siirtyessa.)
# syklinPituusKorjaus on mittaussyklin ulkopuolinen aika eli noin 50-70 millisekuntia. Tarkempi arvo voidaan mitata, kun muut muuttujat vakioidaan.

lahetettavanDatanPituusMinuutteina=int(round(float(purskeidenLukemisVali)*mittausPurskeita/60)); # 30 s * 2 / 60 --> 1 min
if lahetettavanDatanPituusMinuutteina<1:
	lahetettavanDatanPituusMinuutteina=1;

#### TESTIASETUKSET - TODO voidaan poistaa lopullisesta ohjelmistosta ######################################################################################## -- ##

global fakeTimeSpeedUp
fakeTimeSpeedUp=testiasetus['test']['fakeTimeSpeedUp']; # True, kun nopeutetaan ajan kulutumista. Kaytetaan simuloidun datan tuottamiseen palvelimelle.
	
OhitaAlunTauko=testiasetus['test']['OhitaAlunTauko']; # True, kun ohitetaan alun tauko. Testivaiheessa tiedetaan milloin viesti on odotettavissa, eika tarvitse odottaa. OhitaAlunTauko=True;

automaattinenNollaVirranKalibrointi=kalibrointiasetus['kalibrointi']['automaattinenNollaVirranKalibrointi'];

RaspberryPi3=False; # Kun laitetta ajetaan Raspi3:ssa tapahtuvat kaikki mittaukset noin 9 kertaa nopeammin
if RaspberryPi3:
	mittauksiaSekunninVerran=mittauksiaSekunnissa*9;

def printtaaAikaleima(aikaleimaIn): # TODO voidaan poistaa lopullisesta. Kaytetaan vain, kun fakeTimeSpeedUp.
	kelloJaPaiva=datetime.datetime.fromtimestamp(
		int(aikaleimaIn)
		).strftime('%Y-%m-%d %H:%M:%S');
	print("- Mittausten aikaleima on: {0} - pwm ja time: {1}".format(aikaleimaIn, kelloJaPaiva)
	)

if fakeTimeSpeedUp: # TODO voidaan poistaa lopullisesta. Kaytetaan vain, kun generoidaan simuloitua dataa palvelimelle.
	global fakeStarttiAika;
	global fakeKierrosLaskuri;
	fakeStarttiAika = int(round(time.time())); # aikaleima, timestamp in s 
	fakeKierrosLaskuri=0;	

# -------------------- Kommunikaation testausasetuksia ----------------------- # TODO voidaan poistaa lopullisesta. 
LoraJoinedAtStart=testiasetus['test']['LoraJoinedAtStart']; #False; # False - default # Lora JOINED when START - skip init and JOIN # TODO korvaa RM186test -komennolla
GPRSJoinedAtStart=testiasetus['test']['GPRSJoinedAtStart']; #False; # False - default # GPRS JOINED when START - skip init

# -------------------- Mittauksen testausasetuksia -----------------------
saveData=testiasetus['test']['saveData']; #True

if BTmode:
	import BTcom;
	global viestiBTlaitteelle1; global viestiBTlaitteelle2; global viestiBTlaitteelle3; global viestiBTlaitteelle4;
	viestiBTlaitteelle1=""; viestiBTlaitteelle2=""; viestiBTlaitteelle3=""; viestiBTlaitteelle4=""
	global vastausBTlaitteelta1; global vastausBTlaitteelta2; global vastausBTlaitteelta3; global vastausBTlaitteelta4;
	vastausBTlaitteelta1=""; vastausBTlaitteelta2=""; vastausBTlaitteelta3=""; vastausBTlaitteelta4="";
	BTlaite_lkm=kommunikaatioasetus['BT']['BTlaite_lkm'];

global kelloSynkroituViimeksi; #Alustetaan synkronointiaika tarpeeksi kauas
nykyhetki = datetime.datetime.now();
kelloSynkroituViimeksi = nykyhetki - datetime.timedelta(30); # kuukausi sitten
	
if ethernetMode: # yhdistetty Ethernet-asetukset testauksen helpottamiseksi 
	import ETHERNETcom; # Kaytetaan olemassa olevaa internet-yhteytta
	GPRSMode = False # True; # 1, jos GPRS-COMM-laite
	LoraMode = False # False; # 1, jos Lora-laite
	# BTmode = False;	# True, jos BT-laite GPRS:n alaisuudessa

# -------------------- debug-asetuksia -----------------------
kerroAsetukset=testiasetus['test']['kerroAsetukset']; # True; # kun 1, niin naytetaan laite-asetukset

# testiasetus['test'][' ']; #
#### TEST-SETTINGS - END  ######################################################################################## -- ##

import RPi.GPIO; # RPi.GPIO as GPIO
# import Adafruit_GPIO as GPIO # vaihtoehtoinen GPIO-kirjasto
import Adafruit_GPIO.SPI as SPI; 
import Adafruit_MCP3008; 

# Communication import #serial # Lora-import # GPRS-import # BT-import
import GPIOhallinta; # GPIO:n hallinta ja siihen liittyvat komennot
import serial; # sarjaliikenne
import LORAcom; # UART-komennot Lora-radion kayttoon # 1a. kommunikointi Laird RM186 -modulin kanssa
import GPRScom; # UART-komennot GSMradion kayttoon	# 1b. kommunikointi SIMCOM800F GSM-modulin kanssa
import mittausMCP3008 # mittausten lukeminen SPI-vaylan kautta

############################### Kommunikaation konffaus ########################################
#define serial port settings # see import serial: ser.write ser.read ser.readline
ser = serial.Serial(
	port='/dev/ttyAMA0',
	baudrate = 115200,
	parity=serial.PARITY_NONE,
	stopbits=serial.STOPBITS_ONE,
	bytesize=serial.EIGHTBITS,
	timeout=5
	)

# IF LORA - setting
shakey=kommunikaatioasetus['com']['shakey'];
binaryshakey=kommunikaatioasetus['com']['binaryshakey'];

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
global sendFailedCountToday, sendFailedCountInRow, sendSucceedCountInRow
sendFailedCountToday=0;
sendFailedCountInRow=0;
sendSucceedCountInRow=0;

error=0 ;	# if error=10 then reset the RM186 CHIP

# ------------------------------------------------------------------#

# Asetetaan ohjattavat Raspin pinnit
katkoOhjaus=0; # 0 = ei katkoa eli rele johtaa; 1 = katko paalla eli rele vedetaan auki ja virta katkaistaan

# -------------------- MCP3008 - IO luku ja kalibroinnnit ----------------------- # asetukset on luettu tiedostosta
# tallennusVali = purskeidenLukemisVali * mittausPurskeita = 300 # 10 x 30 s eli aika joka odotetaan ennen uutta tallennuskierrosta

mittausKierroksenKestoSekunteina = mittausPurskeita * purskeidenLukemisVali; # 300 # old mittausKierroksenKestoSekunteina = mittausKierroksenKestoMinuutteina * 60 # 5 * 60 = 300
mittausKierroksenKestoMinuutteina = int(round(float(mittausKierroksenKestoSekunteina)/60)) # 5 # minuuttia
if mittausKierroksenKestoMinuutteina==0:
	mittausKierroksenKestoMinuutteina=1;
	debug("Nyt mittauskierros kestaa alle minuutin!  Tallaista tilannetta ei pitaisi tulla, koska pollausvalin palvelimelle ei tule olla alle 1 minuutti.")

kommunikaatioValinPituusSekunteina=int(round(mittauksiaTallennetaan * mittausKierroksenKestoSekunteina))
if kommunikaatioValinPituusSekunteina==0: # Taysin teoreettinen tilanne, mutta estetaan mahdollinen nollalla jakaminen
	kommunikaatioValinPituusSekunteina=1;


kommunikaatioValinPituus = int(round(float(kommunikaatioValinPituusSekunteina)/60)) ; # 30 minuuttia. mittauksia tallennetaan x 5 minuutti
if kommunikaatioValinPituus==0:
	kommunikaatioValinPituus=1;
	debug("Nyt kommunikaatiosykli kestaa alle minuutin!  Tallaista tilannetta ei pitaisi tulla, koska pollausvalin palvelimelle ei tule olla alle 1 minuutti.")

## kierrosmaarat ajastettuja tarkastuksia varten
kierroksiaTunnissa=int(round(3600.0/kommunikaatioValinPituusSekunteina)); # kommunikaatioValinPituus on valin kesto minuutteina
kierroksiaVuorokaudessa=int(round(24*3600.0/kommunikaatioValinPituusSekunteina));
kierroksiaKuukaudessa=int(round(30*kierroksiaVuorokaudessa));


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
	
	debug("Oma laite (omaLaiteID): {0} ; BTlaiteID1: {1}".format(omaLaiteID, BTlaiteID1));
	
	if GPRSMode:
		debug("GPRS-COMM-laite SIMCOM 800F kaytossa");
		## TODO voidaan poistaa asetusten osoitus nayttoon
		nimi=kommunikaatioasetus['GPRS']['laite_nimi']; # basicAuth asetukset
		pw=kommunikaatioasetus['GPRS']['laite_pw']; # basicAuth asetukset
		postURL=kommunikaatioasetus['GPRS']['postURL']; # esim. postURL="jouko.smartip.cl:8080/postia"; # mm. apache2:n kautta toimii 
				
		debug("BasicAuth-asetukset Laitenimi: {0} ; pw: {1}. \n HTTPS-post viestit lahetetaan osoitteeseen: \n  {2} ".format(nimi, pw, postURL)); ## TODO poista lopullisesta
	if ethernetMode:
		nimi=kommunikaatioasetus['GPRS']['laite_nimi']; # basicAuth asetukset
		pw=kommunikaatioasetus['GPRS']['laite_pw']; # basicAuth asetukset
		postURL=kommunikaatioasetus['GPRS']['postURL']; # esim. postURL="jouko.smartip.cl:8080/postia"; # mm. apache2:n kautta toimii 
		debug("BasicAuth-asetukset Laitenimi: {0} ; pw: {1}. \n HTTPS-post viestit lahetetaan osoitteeseen: \n  {2} ".format(nimi, pw, postURL)); ## TODO poista lopullisesta
		
	if LoraMode:
		debug("Lora-kommunikaatio kaytossa");
		debug("Salausasetukset shakey: {0} ; pw: {1}. \n".format(shakey, binaryshakey)); # TODO poista tai salaa ## TODO poista lopullisesta
		
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
global ohjelmanStatus; # Muuttuja, joka kertoo ohjelman suorituksen etenevan normaalisti
ohjelmanStatus=1;

global tallennuksia; # turha?
tallennuksia=0;

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
# Ohjelmistopaivityksen muuttujia

global paivitaSofta; # Tarkastetaan mittausten palvelimelle lahetyksen jalkeen.
paivitaSofta=False; # bitti joka nousee ylos, kun softa on ladattu ja koostettu valmiiksi. 

splitSize=128; fileParts=0; # alustukset
global paivitysKansio; global smartBasicKansio; global asennettuVersionumero;
# paivitysKansio="paivitysTiedostonPalat"; 
paivitysKansio=paivitysasetus['paivitys']['paivitysKansio']; # kansio, johon palat ladataan
smartBasicKansio=paivitysasetus['paivitys']['smartBasicKansio']; # kansio, josta smartBasic asennetaan
asennettuVersionumero=paivitysasetus['paivitys']['asennettuVersionumero'];

global joinedFile; # RM186-moduliin paivitettavan tiedoston nimi. Oletusnimi tallennukselle.
joinedFile="cmd.uwf";


global tallennuspolku; # old splitFolder="splittedUpdateFile";
nykyinenPolku = os.getcwd()

tallennuspolku=os.path.join(nykyinenPolku, paivitysKansio)

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
	debug("Ykkoset on {0}".format(ykkoset))
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
	global kelloSynkroituViimeksi;
	nykyhetki = datetime.datetime.now();

	if LoraMode:
		aikaaSynkronoinnista=nykyhetki-kelloSynkroituViimeksi;
		if aikaaSynkronoinnista.days==0 and aikaaSynkronoinnista.seconds<65*60:
			debug("Ohitetaan kellosynkronointi, silla edellisesta synkroinnista on alle tunti 5 minuuttia. ") # Kyseessa on vain Thingparkin puskuriin jaanyt toisteinen synkronointiviesti.
			debug("Viimeksi synkronointiin: {0} minuuttia sitten.".format((aikaaSynkronoinnista.seconds)/60));
			return
	
	debug ("Korjataan jarjestelmakelloa.")

	# erotus = JouKo-palvelimen-aika - raspin_aika	(OLI: # erotus = TP-aika - raspin_aika)
	# erotus kertoo paljonko Raspin kello on jaljessa.

	# Asetetaan laitteiden kellot aidosti oikeaan aikaan, etta katkot astuvat voimaan tasmalleen haluttuna aikana. 
	# Nama 'viive'-asetukset riippuvat viestien toimitusajasta Jouko-palvelimelle eli kaytannossa kommunikaatiolaitteiden ja palvelimen nopeuksista, kuormitusasteesta ja resursseista.
	# Kun jarjestelma on laadittu hyvin, voidaan viiveet helposti arvioida 1 sekunnin tarkkuudella.
	# Ilman tata korjausta katkot alkavat muutamaa sekuntia liian aikaisin.
	loraViestinKokonaisToimitusAikams=27000; # Palvelimen mielesta laitekello jaa pysyvasti taman verran virheelliseen aikaan.
	GPRSViestinKokonaisToimitusAikams=7500;
	if LoraMode:
		erotus=erotus-loraViestinKokonaisToimitusAikams;
	if GPRSMode:
		erotus=erotus-GPRSViestinKokonaisToimitusAikams;
		
	korjattuAika = nykyhetki + datetime.timedelta(milliseconds=erotus);
	

	debug (" - Vanha jarjestelmakello: {0} ; korjattuAika: {1} ; kelloa siirrettiin {2} ms".format(nykyhetki, korjattuAika, erotus));
	
	debug ("Asetetaan jarjestelmakello: (varmista laitteen asetuksista, etta kellon automaattinen paivitys ei ole paalla eli 'time-auto-update is OFF')");
	os.system('sudo date -s "%s"' % korjattuAika);

	nykyhetki2 = datetime.datetime.now();
	debug ("Uusi kellonaika: {0}".format(nykyhetki2));
	kelloSynkroituViimeksi=korjattuAika; # Talteen, ettei Loraa synkronoida liian usein
	
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
	# Asetetaan tallennuspolku pois tyoskentelykansiosta
	kohdetiedosto=os.path.join('.', paivitysKansio, dest_file)
	#kohdetiedosto='./'+paivitysKansio+'/'+dest_file;

	# Create a new destination file
	output_file = open(kohdetiedosto, 'wb');
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
	tyhjennysOnnistui=False;
	if LoraMode or BTmode: # lisaa 'or BTslaveMode' jos paivitystoiminto lisataan
		tyhjennysOnnistui=LORAcom.tyhjennaRM186flash();
	if tyhjennysOnnistui:
		debug("Paivitetaan RM186-modulin Smart Basic -ohjelmisto.");
		if LoraMode: # Lora-laite, paivitetaan cmd-ohjelma
			ajettavaOhjelma="./lataa_Lora_SB.bat"; # 'Central': cmd
			
		if BTmode: # GPRS-laite BT-moodissa eli BT Central-laite
			ajettavaOhjelma="./lataa_BT_CE_SB.bat"; # BT-Central: VSPC eli VSP2 (BT-laite2 - skannaa)
			
		if BTslaveMode: # Kytkinlaite, jossa vain BT-radio eli BT Peripheral-laite
			debug("Toistaiseksi ei ole kaytossa automaattista paivitystoimintoa BT-slavelaitteen ohjelmistolle.")
			debug("Tama komento on laadittu valmiiksi, jos tama ominaisuus lisataan myohemmin.")
			ajettavaOhjelma="./lataa_BT_PE_SB.bat"; # BT-Peripheral: VSPP eli VSP1 (BT-laite1 - mainostaa)
			
		# ajaOhjelmaOS(ajettavaOhjelma);
		try:
			ajaOhjelmaOS(ajettavaOhjelma);
		except:
			debug("Tanne ei pitaisi koskaan tulla, silla talloin paivitysprosessi on toteutettu puuttteellisesti.");
			debug("Mahdollisessa FLASH-paivityksen ongelmatilanteessa, paivitystiedosto oli viallinen ja RM186 on epamaaraisessa tilassa.")

		debug("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
		debug("RM186-piirin ohjelmisto on paivitetty.")
		
		LORAcom.UARTsyncLaird();
		
		# Kaynnistetaan radion ohjelmisto uudelleen
		debug("Alustetaan Lora-radio uudelleen.");
		
		if LoraMode: # Tama tai alempi
			LORAcom.LoraInitAll()
		
		if LoraMode: 
			pass;
			# alustaKommunikaatioLaite(); # kaynnistetaan kommunikaatiolaitteet
			# alustaKommunikaatioSofta(False); # kaynnistetaan kommunikaatiolaitteiden ohjelmistot, ei synkronoida kelloa, ettei palvelin ruuhkaudu mahdollisessa ongelmatilanteessa
			
		if BTmode:
			pass;
			# alustaKommunikaatioSofta(False); # kaynnistetaan kommunikaatiolaitteiden ohjelmistot, ei synkronoida kelloa, ettei palvelin ruuhkaudu mahdollisessa ongelmatilanteessa
			
		if BTslaveMode:
			debug("Ei toistaiseksi automaattista paivitystoimintoa BT-slavelaitteelle")
			pass;


################# Kommunikaatio - viestien kasittely -funktioita #################################

def pakkaaViestidata(viesti):
	pakattuViesti="none";
	viestiStr=str(viesti);
	if "mittaukset" in viesti:
		debug("pakataan mittausviesti")
		pakattuViesti=viestinpurku.pakkaa_viesti("mittaukset", viesti); # viesti pakataan aina - GPRS ja LoRa
	
	viestiStr=str(viesti)
		
	if "laiteaika" in viestiStr:
		debug("pakataan synkronointiviesti")
		pakattuViesti=viestinpurku.pakkaa_viesti("aikasynk", viesti); # viesti pakataan aina - GPRS ja LoRa

	# if "viestityyppi in viesti: # if more messagetype --> add lines here - pakataan eri tavalla
		# TODO tahan lisaa viestityyppeja, jos niita tulee
	debug("Viestidata on ennen pakkausta:" + str(viesti));
	debug("Viestidata on pakkauksen jalkeen:" + str(pakattuViesti));
	
	return pakattuViesti;

def puraViestidata(viestidata):
	purettuViestidata=viestidata;
	return purettuViestidata;


## Paluuviestien kasittely
# -------------------viestien vastaanotto palvelimelta -----------------------------
def handleServerReply(replyMessage):
	debug("------------------------- saapuneen viestin kasittely alkaa ---------------------------------------------")
	palvelimenAikaSynkVastaus={} # tama funktio palauttaa erotuksen, jos laite synkronoidaan.
	debug("Kasitellaan purettua palvelimelta saapunutta viestia, jonka pitaisi olla DICT-objekti:")
	debug(replyMessage);
	if (not isinstance(replyMessage, dict)):
		debug("ERROR: Palvelimen paluuviesti ei ole 'dict-object'")
		return
		
	messageType=0
	global paivitaSofta;
	global paivitysKansio; global smartBasicKansio; global asennettuVersionumero;
	global tallennuspolku; 
	global joinedFile; #  RM186-moduliin paivitettavan tiedoston nimi # kaytetaan tata, jos muuta nimea ei kerrota

	viestiTyyppi = next(iter(replyMessage)) # viestin tyyppi stringina # mita tama tekee? Ilmo
	debug("viestiTyyppi luettuna protobuf-viestista: " + viestiTyyppi);
	
	if viestiTyyppi==0: # viestiTyyppi==0: # ei tunnistettua viestia
		debug("Ei suoritettavaa palvelimelta.");
		return

	#if "viestityyppi_tahan_kohtaan" in replyMessage: # katkoo vain dict-objektin uloimman avaimen		
	if "aikasynk" in replyMessage: # kasitellaan synkronointiviesti
		messageType=3; # test3=saatuData_str.find('aikasynk'); # {"aikasynk": {"erotus": 5}} - HUOM: erotus millisekunteina. TP-raspi
		
		aikasynk=replyMessage['aikasynk'] # koska DICT-objekti
		erotus=aikasynk['erotus'] # koska DICT-objekti
					
		debug ("Korjataan kelloa loopin loputtua erotuksen verran. Erotus on: " + str(erotus));
					
		integeritOK=False;
		try:
			debug("Ennen INT: {0}".format(erotus))
			erotus=int(erotus);
			debug("Jalkeen INT: {0}".format(erotus))
			if isinstance(erotus, int) or isinstance(erotus, long):
				integeritOK=True;
				debug("Is instance toimii Raspissa.")
		except:
			debug("Erotus ei ollut integer tai long.");
		
		if integeritOK:
			## Synkronoidaan vasta loopin jalkeen.
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
				debug("Tiedot eivat olleet int-muotoisia.")

			kelloNyt = int(round(time.time()*1)) # timestamp in sec
			debug ("KelloNyt on :" + str(kelloNyt));
			katkonAlkuun = katkonAlku - kelloNyt;
			debug ("KatkonAlkuun :" + str(katkonAlkuun));
			katkonKesto = katkonLoppu - katkonAlku;
			debug ("katkonKesto :" + str(katkonKesto));
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
			katkoSQL.tarkastaKatkotaulu(60); # SQL # luetaan tietokanta lapi ja tehdaan katkoille tarvittavat toimenpiteet # SQL # Luodaan saikeet, jos seuraavan minuutin aika alkava katko
				
	if "katkonestot" in replyMessage:
		messageType=5; # test5=saatuData_str.find('katkonestot'); # {"katkonestot":[{"katkoID": 5}, {"katkoID": 8}]} 
		# katkoestetty

		debug("Katkonesto-viesti saapunut. Paluuviesti on : {0}".format(replyMessage));
		katkonEstoLista=[];
		katkoja=0;
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
			debug("katkoTiedot: {0}".format(katkoTiedot))
			laskuri=laskuri+1;
			katkoID=katkoTiedot['katkoID'];
			debug("katkoID: {0}".format(katkoID))
			try:
				katkoID=int(katkoID)
				if isinstance(katkoID, int):
					integeritOK=True;
			except:
				debug("KatkoID ei ollut integer.")
			if integeritOK:
				debug("Poistetaan tietokannasta. KatkoID: {0}".format(katkoID))
				
				katkoSQL.poistaYksiKatkotieto(katkoID);
				pass;
				
		
	if "sbUpdateStart" in replyMessage:
		messageType=7; # test7=saatuData_str.find('sbUpdateStart'); # {"sbUpdateStart": {"numFiles": 35}}
		# paivitysalkaa
		
		debug("Paivitys alkaa viesti saapunut. ");
		tiedostojenLkm=0;
		# saatuData_obj=json.loads(replyMessage); # jos JSON
		# tiedostojenLkm=saatuData_obj['sbUpdateStart']['numFiles'];
		tiedostojenLkm=replyMessage['sbUpdateStart']['numFiles']
		debug ("tiedostojenLkm :" + str(tiedostojenLkm));

		import errno
		import shutil

		debug("Luodaan kansio: {0}".format(paivitysKansio)); # Luodaan tyhja kansio ja varmistetaan sen olevan tyhja.
		try:
			os.makedirs(paivitysKansio)
		except OSError as e:
			debug("Kansio on jo olemassa.")
			if e.errno != errno.EEXIST:
				debug("Jokin muu virhe kansion luomisessa.")
		
		nykyinenPolku = os.getcwd()
		debug("Nykyinen tyoskentelypolku: {0}".format(nykyinenPolku));

		tallennuspolku=os.path.join(nykyinenPolku, paivitysKansio); #tallennuspolku=nykyinenPolku+'/'+paivitysKansio
				
		debug("Tyhjennetaan kansio: {0}".format(tallennuspolku));
		
		for the_file in os.listdir(tallennuspolku):
			file_path = os.path.join(tallennuspolku, the_file)
			try:
				if os.path.isfile(file_path):
					os.unlink(file_path)
				#elif os.path.isdir(file_path): shutil.rmtree(file_path); # voitaisiin poistaa myos alihakemistot
			except Exception as e:
				debug(e)

	if "sbUpdatePart" in replyMessage:
		import base64;

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
		try:
			paivitysPalaTiedot=replyMessage['sbUpdatePart'];
			paivitysPalaNum=paivitysPalaTiedot['num']
			paivitysPalaData64=paivitysPalaTiedot['part'];
			tiedostonnimi="part"+str(paivitysPalaNum).zfill(5);
			debug ("base64data: " + str(paivitysPalaData64));
			paivitysPalaDataBinaryStr=base64.b64decode(paivitysPalaData64);
			textStr=paivitysPalaDataBinaryStr.decode('utf-8')
			debug ("paivitysPalaData: " + str(textStr));

			tiedostonKokoPolku=os.path.join(tallennuspolku,tiedostonnimi)
			debug("Tallennetaan vastaanotettu paivitystiedoston pala: {0}".format(tiedostonKokoPolku))
			overWriteData(tiedostonKokoPolku,textStr);
		except:
			debug("Tiedostopalan vastaanottaminen ei onnistunut. Mahdollisesti virheellinen sisalto (ei base64).")
		
	if "sbUpdateStop" in replyMessage:
		messageType=9; # test9=saatuData_str.find('sbUpdateStop'); #{"sbUpdateStop": {"splitSize": 128, "numFiles": 35}} 
		# viesti={"sbUpdateStop": {"splitSize": 128, "numFiles": 2, "fileName": "tiedostonnimi.json", "versioNumero": 10}}

		# paivitys odottaa asentamista
		debug("paivitys loppuu viesti. Koostetaan tiedosto ja ajetaan paivitys.");
			
		tiedostojenLkm=0;
		testOK=False; # Tarkastetaan, etta paivityskansio ja tiedostot ovat olemassa ja voidaan ajaa paivitys.
		versionumeroOK=False;
		splitSize=0
		tiedostojenLkm=0
		tallennettavanTiedostonNimi="Ei_nimea"
		versionumero=0

		try:
			paivitysLoppuuTiedot=replyMessage['sbUpdateStop'];
			debug("stop OK")
			splitSize=paivitysLoppuuTiedot['splitSize'];
			debug("size OK")
			tiedostojenLkm=paivitysLoppuuTiedot['numFiles'];
			debug("num OK")
			tallennettavanTiedostonNimi=paivitysLoppuuTiedot['fileName']; # tallennettavanTiedostonNimi=joinedFile; # asetetaan oletuksena paivitystiedoston nimeksi 'cmd.uwf'
			debug("fileName OK")
			versionumero=paivitysLoppuuTiedot['versioNumero']; # versionumero=0;
			debug("versioNumero OK")
		except:
			debug("Jotain tietoja puuttui. Ei paiviteta.")
			return palvelimenAikaSynkVastaus;
			
		debug("UpdateStop Viestidata -- splitSize: {0} ; tiedostojenLkm: {1} ; tallennettavanTiedostonNimi: {2} ; versionumero: {3}".format(splitSize, tiedostojenLkm, tallennettavanTiedostonNimi, versionumero))
		
		versionnumeroOnNumero=isinstance(versionumero, int)
		if versionnumeroOnNumero:
			if versionumero>asennettuVersionumero:
				debug("Versionumero on integer ja suurempi kuin jo asennettu versio. OK.")
				versionumeroOK=True;
	
		if not versionumeroOK:
			debug("Lopetaan paivitysprosessi, koska paivityksen versio on vanha.")
			debug("Saapui viesti, joka kasiteltiin. Viestityyppi oli: "+str(messageType));
			return palvelimenAikaSynkVastaus;

		debug ("Koostetaan paivitys: " + str(tiedostojenLkm) + " kpl, " + str(splitSize) +" byten tiedostoa ");
		partnum=0;
		
		parts = os.listdir(tallennuspolku) # Get a list of the file parts
		parts.sort() # Sort them by name (remember that the order num is part of the file name)
		debug("Kansiossa pitaisi olla: {0} tiedostoa. Siella on seuraavat tiedostot: {1}".format(tiedostojenLkm, parts))

		# laske lukumaara
		oikeitaPaloja=0;
		for i in range(0, tiedostojenLkm):
			partnum += 1;
			tiedostopalanNimi = os.path.join(tallennuspolku, 'part'+str(partnum).zfill(5))
			debug("Tarkistetaan, etta tiedostopala on kansiossa: {0}".format(tiedostopalanNimi));
			try:
				loydetty=os.path.isfile(tiedostopalanNimi)
			except:
				loydetty=False;
			if loydetty:
				oikeitaPaloja+=1;
		
		debug("Paloja loydetty: {0} kpl.".format(oikeitaPaloja))
		if oikeitaPaloja==tiedostojenLkm:
			debug("Kaikki palat kansiossa. Ajetaan join.")
			testOK=True;
		
		## Paivitystiedosto on koostettu. Asennetaan se kayttoon soveltuvalla tavalla.
		hyvaksyttavatTiedostotSB=""
		if LoraMode:
			hyvaksyttavatTiedostotSB=" cmd.uwf "; # cmd = LORA-kommunikaatio-ohjelma
		if BTmode:
			hyvaksyttavatTiedostotSB=" vspc.uwf VSPC.uwf "; # VSPC = BT Central -kommunikaatio-ohjelma
			
		hyvaksyttavatTiedostotJSON=" tiedostonnimi.json, testi.txt, asetukset.json, kalibrointi.json, kommunikaatio.json, testiasetukset.json, toimintatila.json "
		# hyvaksyttavatTiedostotJSON="asetukset.json, kalibrointi.json, toimintatila.json"
		
		hyvaksyttavaSB=hyvaksyttavatTiedostotSB.find(tallennettavanTiedostonNimi) # ajetaan paivitys vain, jos paivitystiedoston nimi on hyvaksyttava
		hyvaksyttavaJSON=hyvaksyttavatTiedostotJSON.find(tallennettavanTiedostonNimi) # ajetaan paivitys vain, jos paivitystiedoston nimi on hyvaksyttava
		
		debug("hyvaksyttavaSB: {0}".format(hyvaksyttavaSB))
		debug("hyvaksyttavaJSON: {0}".format(hyvaksyttavaJSON))

		SBtestOK=False;
		JSONtestOK=False;
				
		# Selvitetaan minka tyyppinen (SB vai json) paivitystiedosto ladattiin ja onko se sallittujen paivitysten joukossa.
		if hyvaksyttavaSB>=0: # ('tallennettavanTiedostonNimi' in hyvaksyttavatTiedostotSB): 
			debug("Paivitystiedostonnimi: {0} loytyy hyvaksyttavien SB-tiedostonnimien listasta: {1}".format(tallennettavanTiedostonNimi, hyvaksyttavatTiedostotSB))
			SBtestOK=True; 
			
		if hyvaksyttavaJSON>=0: # ('tallennettavanTiedostonNimi' in hyvaksyttavatTiedostotJSON): 
			debug("Paivitystiedostonnimi: {0} loytyy hyvaksyttavien JSON-tiedostonnimien listasta: {1}".format(tallennettavanTiedostonNimi, hyvaksyttavatTiedostotJSON))
			JSONtestOK=True; 
		
		joinOnnistui=False;		
		if testOK: # Ajetaan vain, kun kaikki tiedostot kansiossa ja tiedonton nimi on oikea.
			try:
				join(tallennuspolku, tallennettavanTiedostonNimi, splitSize);
				joinOnnistui=True;
			except:
				debug("Join ei onnistunut.") # joinOnnistui=False;
				# paivitaSofta=False;
		
		
		if joinOnnistui:
			debug ("Tiedosto koottu yhteen: "+ tallennettavanTiedostonNimi);
				
			nykyinenPolku = os.getcwd()
			
			TiedostonSijainti=os.path.join(nykyinenPolku, paivitysKansio, tallennettavanTiedostonNimi); #TiedostonSijainti=paivitysKansio+'/'+tallennettavanTiedostonNimi;
			TiedostonKohdeSijainti=os.path.join(nykyinenPolku, smartBasicKansio, tallennettavanTiedostonNimi); #TiedostonKohdeSijainti=smartBasicKansio+'/'+tallennettavanTiedostonNimi;
			vanhatiedostoJemmaan=tallennettavanTiedostonNimi+'.old'
			VanhaTiedostonKohdeSijainti=os.path.join(nykyinenPolku, smartBasicKansio, vanhatiedostoJemmaan); #VanhaTiedostonKohdeSijainti=smartBasicKansio+'/'+tallennettavanTiedostonNimi+'.old';
			
			JSONTiedostonKohdeSijainti=os.path.join(nykyinenPolku, tallennettavanTiedostonNimi); # JSONTiedostonKohdeSijainti='.'+'/'+tallennettavanTiedostonNimi;
			VanhanJSONTiedostonKohdeSijainti=os.path.join(nykyinenPolku, vanhatiedostoJemmaan); # VanhanJSONTiedostonKohdeSijainti='.'+'/'+tallennettavanTiedostonNimi+'.old';
			
			if SBtestOK: # global paivitysKansio; global smartBasicKansio
				debug("Saatiin palvelimelta SB-paivitystiedosto.") # tiedosto on joko cmd.uwf tai VPSC.uwf
								
				try: # vanha SB-versio jemmaan VanhaTiedostonKohdeSijainti
					ajettavaKomento="cp {0} {1}".format(TiedostonKohdeSijainti, VanhaTiedostonKohdeSijainti)
					debug("Ajetaan komento {0}".format(ajettavaKomento));
					ajaOhjelmaOS(ajettavaKomento)
				except:
					debug("Tiedoston kopioiminen jemmaan ei onnistunut.")

				try:
					debug("Kopioidaan tiedosto smartBasic-kansioon:  TiedostonSijainti --> TiedostonKohdeSijainti");
					ajettavaKomento="cp {0} {1}".format(TiedostonSijainti, TiedostonKohdeSijainti);
					debug("Ajetaan komento {0}".format(ajettavaKomento));
					ajaOhjelmaOS(ajettavaKomento);
				except:
					debug("SB Tiedoston kopioiminen paivitettavaksi ei onnistunut.")

				# valmiit SB-asennuskomennot
				debug("Alustetaan komennot")
				asennaLoraSmartBasic=os.path.join('.', 'lataa_Lora_SB.bat');
				asennaBTCentralSmartBasic=os.path.join('.', 'lataa_BT_CE_SB.bat');
				asennaBTPeripheralSmartBasic=os.path.join('.', 'lataa_BT_PE_SB.bat'); # toistaiseksi tarpeeton
				
				if LoraMode:
					debug("Paivitetaan Lora-kommunikaation smartBasic-ohjelmisto")
					ajaOhjelmaOS(asennaLoraSmartBasic)
					
				if BTmode:
					debug("Paivitetaan BT-kommunikaation smartBasic-ohjelmisto")		
					ajaOhjelmaOS(asennaBTCentralSmartBasic)
			
			if JSONtestOK:
				debug("Saatiin palvelimelta asetusten paivitystiedosto (JSON) ja koottiin se onnistuneesti.")
				# Ladataan json-tiedosto muistiin, ja jos se on validi, otetaan kayttoon.
				otetaanJSONkayttoon=False
				try:
					pass;
					debug("Testataan ladattu JSON oikeelliseksi.")

					with open(TiedostonSijainti) as json_testaus_file:
						debug("Avataan JSON tiedosto testausta varten. Mikali rakenne ei ole oikeellinen, ei tiedostoa voida kayttaa.")
						testataanJSONtiedosto = json.load(json_testaus_file)
					# tassa voitaisiin testata kaikki rakenteet tiedostokohtaisesti
					otetaanJSONkayttoon=True;
				except:
					debug("Puutteellinen json-tiedosto. Ohitetaan.")
					
				if otetaanJSONkayttoon:
					# vanha tiedosto jemmaan
					try:
						ajettavaKomento="cp {0} {1}".format(JSONTiedostonKohdeSijainti, VanhanJSONTiedostonKohdeSijainti)
						debug("Ajetaan komento {0}".format(ajettavaKomento));
						ajaOhjelmaOS(ajettavaKomento)
					except:
						debug("Tiedoston kopioiminen jemmaan ei onnistunut.")

					try:	
						# Kopioidaan tiedosto tyoskelykansioon
						ajettavaKomento="cp {0} {1}".format(TiedostonSijainti, JSONTiedostonKohdeSijainti)
						debug("Ajetaan komento {0}".format(ajettavaKomento));
						ajaOhjelmaOS(ajettavaKomento)
					except:
						debug("JSON tiedoston kopioiminen kayttoon ei onnistunut.")
								
			if SBtestOK: 
				debug ("Nostetaan paivitaSofta-bitti ylos ja paivitetaan seuraavan viestin lahetyksen jalkeen, jos ei ole katkoja tulossa.")
				paivitaSofta=True; # Jos paivitys on uwf-tiedosto, niin paivitetaan SmartBasic-softa.
			if JSONtestOK:
				debug("Paivitettiin JSON-asetustiedosto jouko-kansioon. Kaynnistetaan Raspberry uudelleen, etta paivitys astuu voimaan.")
				resetSelf(); 
			
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

def radioConnectionReady():
	debug("Kevyt tarkistus, etta palvelimen suuntaan kommunikoiva radiolaite vastaa kuten pitaakin.")
	kunnossa=False
	if GPRSMode:
		if True: # Pikatesti, UART OK.
			kunnossa=GPRScom.RadioTestOK(); 
		if False: # Tarkastetaan, etta on saatu IP-osoite.
			reply=GPRScom.queryIPaddress();
			if ("OK" in reply):
				kunnossa=True;
	if LoraMode:
		debug("Tarkastetaan RM186test, DataRate ja LoraJoin-tila")
		reply=LORAcom.LoraRadioTestOK();
		if reply==True:
			kunnossa=True;
	return kunnossa;
			

def resetRadioConnection(): # TODO vanha komento. Voidaan poistaa
	debug("Annetaan reset Radiolaitteelle.")
	hardResetRadioDevice();
			
def softResetRadioConnection():
	debug("Annetaan ohjelmallinen reset Radiolaitteelle.")
	if GPRSMode:
		reply=GPRScom.softReset();
		pass
	if LoraMode:
		reply=LORAcom.softReset();
		pass
	alustaKommunikaatioLaite(); # Alustetaan radiolaite uudelleen kayttovalmiuteen.
	alustaKommunikaatioSofta(False); # kaynnistetaan kommunikaatiolaitteiden ohjelmistot, ei synkronoida kelloa, ettei palvelin ruuhkaudu mahdollisessa ongelmatilanteessa
	
	
def hardResetRadioDevice():
	debug("Annetaan GPIOn kautta ohjaten fyysinen reset Radiolaitteelle.")
	if GPRSMode:
		GPIOhallinta.UART_to_SIMCOM();
		GPRScom.hardReset()
		pass
	if LoraMode:
		GPIOhallinta.UART_to_LAIRD();
		LORAcom.hardReset()
		pass
	alustaKommunikaatioLaite(); # Alustetaan radiolaite uudelleen kayttovalmiuteen.
	alustaKommunikaatioSofta(False); # kaynnistetaan kommunikaatiolaitteiden ohjelmistot, ei synkronoida kelloa, ettei palvelin ruuhkaudu mahdollisessa ongelmatilanteessa
	
def resetSelf():
	debug("Resetoidaan Linux-tietokone fyysisella resetilla.")
	GPIOhallinta.resetSelf();

	
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
		sendingToGPRS="Lahetetaan viesti JoukoPalvelimelle via GPRS. Viesti: " + str(pakattuViesti);
		debug(sendingToGPRS);
		paluuViesti=GPRScom.sendHTTPmessageWhenGPRSConnected(pakattuViesti);
		
		# tahan valiin voitaisiin tehda SHA256-autentikointi, jos GPRS-viesti. Nyt se ei ole tarpeen, kun kaytossa SSL ja protobuf, seka basic-auth
		# autentikoituVastaus=SHAauth(vastaus)
		
		postViestiToimitettu=GPRScom.onkoPostViestiToimitettu(); # tarkistetaan meniko httpPost-perille, jotta voidaan osoittaa se LED-valolla
		if postViestiToimitettu:
			global vilkutetaanPunaistaLedia;
			vilkutetaanPunaistaLedia=True;
		
		pass;
		
	if LoraMode:
		debug("Lahetetaan viesti JoukoPalvelimelle via Lora. Viesti: " + str(pakattuViesti));
		paluuViesti=LORAcom.LoraSend(pakattuViesti);
		
	if True: # radion lahetysvirheidenhallinta
		if paluuViesti=="RX ERROR": # resetoidaan laite, mikali kommunikaatio jumittaa 3 kertaa perakkain eli luultavasti 30 minuuttia.
			sendFailedCountToday+=1;
			sendFailedCountInRow+=1; 
			if not radioConnectionReady():
				hardResetRadioDevice()
				
			sendSucceedCountInRow=0;
		else:
			sendFailedCountInRow=0;
			sendSucceedCountInRow+=1;
		
		if sendFailedCountInRow==2: # resetoidaan yhteys
			softResetRadioConnection();
		if sendFailedCountInRow==3: 
			hardResetRadioDevice(); # resetoidaan laite, mikali kommunikaatio jumittaa 3 kertaa perakkain eli luultavasti 30 minuuttia.	
			sendFailedCountInRow=0;
		
		if sendFailedCountToday==8:
			resetSelf() # resetoidaan Raspi, jos liikaa kommunikaatiovirheita
			
		if sendSucceedCountInRow>18: # jos 2 tuntia putkeen onnistuneita viesteja, niin nollataan isompi laskuri
			sendFailedCountToday=0;
			
	if ethernetMode:
		debug("Lahetetaan viesti JoukoServerille suoraan olemassa olevan internetyhteyden kautta. Message: " + str(pakattuViesti));
		paluuViesti,errorState=ETHERNETcom.sendHTTPpost(pakattuViesti);
		if errorState:
			debug("Viesti ei mennyt perille. Errorcode: "+str(paluuViesti));
			
	return paluuViesti;

def sendSynkToServer(syyData=0): # olettaa etta yhteys on jo muodostettu
	debug("------------------------- palvelinkommunikaatio alkaa ---------------------------------------------")
	global sendFailedCountToday, sendFailedCountInRow, sendSucceedCountInRow
	
	errorState=False;
	paluuViesti="";
	pakattuViesti="";
	viestiPalvelimelle=""

	
	if GPRSMode: #alusta laite
		# Yhteyden tila varmennetaan GPRScom funktiolla. Ei tarpeen tassa.
		sendingToGPRS="Lahtetaan viesti JoukoServerille via GPRS. Viesti: " + str(viesti);
		debug(sendingToGPRS);
		GPRScom.varmistaRadioEnnenLahetysta();
		GPRScom.alustaHTTPEnnenLahetysta();
		pass;
	
	# Lasketaan paljonko synkronointi kestaa --> saadaan korjausViiveKatkolle
	aikaleimaEnnen = int(round(time.time() * 1000));
	
	# Luodaan Synkronointiviesti	
	synkronointiViesti=luoSynkViesti(syyData)
	
	pakattuViesti=pakkaaViestidata(synkronointiViesti) # viesti pakataan aina - GPRS ja LoRa
	
	if GPRSMode: #lahetetaan viesti, kun radio on jo valmiina
		paluuViesti=GPRScom.lahetaPOSTjaSulje(pakattuViesti);
		aikaleimaJalkeen = int(round(time.time() * 1000));
		korjausViiveKatkolle = aikaleimaJalkeen-aikaleimaEnnen;
		
		debug("korjausViiveKatkolle on: {}".format(korjausViiveKatkolle));
		
		postViestiToimitettu=GPRScom.onkoPostViestiToimitettu(); # tarkistetaan meniko httpPost-perille, jotta voidaan osoittaa se LED-valolla
		if postViestiToimitettu:
			global vilkutetaanPunaistaLedia;
			vilkutetaanPunaistaLedia=True;
		
		pass;
		
	if LoraMode:
		debug("Lahetetaan viesti JoukoServerille via Lora. Viesti: " + str(pakattuViesti));
		paluuViesti=LORAcom.LoraSend(pakattuViesti);
		
	if True: # virheenhallinta
		if paluuViesti=="RX ERROR": # resetoidaan laite, mikali kommunikaatio jumittaa 3 kertaa perakkain eli luultavasti 30 minuuttia.
			sendFailedCountToday+=1;
			sendFailedCountInRow+=1; 
			if not radioConnectionReady():
				hardResetRadioDevice()
				
			sendSucceedCountInRow=0;
		else:
			sendFailedCountInRow=0;
			sendSucceedCountInRow+=1;
		
		if sendFailedCountInRow==2: # resetoidaan yhteys
			softResetRadioConnection(); 
		if sendFailedCountInRow==3: 
			hardResetRadioDevice(); # resetoidaan laite, mikali kommunikaatio jumittaa 3 kertaa perakkain eli luultavasti 30 minuuttia.	
			sendFailedCountInRow=0;
		
		if sendFailedCountToday==10:
			resetSelf() # resetoidaan Raspi, jos liikaa kommunikaatio virheita
			
		if sendSucceedCountInRow>18: # jos 2 tuntia putkeen onnistuneita viesteja, niin nollataan isompi laskuri
			sendFailedCountToday=0;
			
	if ethernetMode:
		debug("Lahetetaan viesti JoukoServerille suoraan olemassa olevan internetyhteyden kautta. Message: " + str(pakattuViesti));
		paluuViesti,errorState=ETHERNETcom.sendHTTPpost(pakattuViesti);
		if errorState:
			debug("Viesti ei mennyt perille. Errorcode: "+str(paluuViesti));
			
	return paluuViesti;

#######################################################################################
# -------------------------- TOP LEVEL COMM ----------------------------------------- #
#######################################################################################

def LoraInitAll(): # turha
	debug("Alustetaan Lora-radio ja ohjelmisto.");
	LORAcom.LairdJoukoInit();
	LORAcom.LoraInit(); # liity verkkoon

def BTInit():
	debug("Jos tarpeen, alustetaan BT-laitteen radio esim. RM186 run VSP1")
	

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

	if LoraMode:
		debug("Lora-kommunikaatio kaytossa. Otetaan Laird-laite kayttoon. ");
		LoraYhteysMuodostettu=False;
		if LoraJoinedAtStart:
			LoraYhteysMuodostettu=LORAcom.LoraGetJoinState() # Varmistetaan onko yhteys luotu.
		
		if (not LoraYhteysMuodostettu):	
			LORAcom.LairdJoukoInit(); #alustaLora();
	if BTmode:
		debug("BT-kommunikaatio kaytossa eli BT-laite on taman GPRS-laitteen alaisuudessa. Luodaan BT-yhteydet.");
		# alustaBT();
		debug("Alusta BT");
	if ethernetMode:
		debug("Kommunikaatiolaitetta ei ole tarpeen alustaa, silla kaytetaan olemassaolevaa internet-yhteytta.")
	if BTslaveMode:
		debug("BT-orjalaitteenkommunikaatio tama laite on BT-orjalaite. BT-mainostaminen alustetaan jo omassa BTslaveCOM-loopissa.");
		# BTcom.BTSlaveInit();
		
def randomTaukoKatkonJalkeen(): 		
	# purskeidenLukemisVali = 30 s, mittausPurskeita = 10, mittauksiaTallennetaan = 2; # 2 x 10 x 30 = 600 s
	randomDelay=(random.randint(0, (mittauksiaTallennetaan*mittausPurskeita*purskeidenLukemisVali))); # arvotaan 0-10min delay 10 * 60 s = 600s 
	debug("Laitteen uudelleen kaynnistys --> Random delay: " + str(randomDelay) + " s");
	if OhitaAlunTauko:
		debug("Ohitetaan alun tauko. Poista kaytosta lopullisesta ohjelmistosta, jotta kaikki laitteet eivat laheta palvelimelle samanaikaisesti.")
		randomDelay=1;
	if randomDelay<0:
		randomDelay=0.001; # Varmistus muuttujan arvolle
	time.sleep(randomDelay);

def kellonSynkronointiLooppi():
	synkronointiEpaonnistui=True;
	epaonnistumisLaskuri=0
	while synkronointiEpaonnistui:
		epaonnistumisLaskuri+=1;
		synkronointiEpaonnistui=kommunikaatioLooppi(omaLaiteID, 2); # just synk
		if epaonnistumisLaskuri>10:
			resetSelf(); # kaynnistetaan Raspi uudelleen, jos yhteys ei toimi
		time.sleep(10)

def alustaKommunikaatioSofta(synkronoidaanKello=True):
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
						softResetRadioConnection();
						seuraavaksiHardReset=True;
					else:
						hardResetRadioDevice();
						seuraavaksiHardReset=False
					time.sleep(1);
			debug("GPRS-yhteys muodostettu OK.")
			vilkutetaanPunaistaLedia=True; # vilkutetaan PUN LED
						
	if LoraMode:
		debug("Lora-kommunikaatio kaytossa. Otetaan Lora-Softa kayttoon. ");
		if (not LoraJoinedAtStart):
			reply=LORAcom.LoraInit(); #alustaLora();
		if synkronoidaanKello:
			kellonSynkronointiLooppi();

	if BTmode:
		debug("BT-kommunikaatio kaytossa eli BT-laite on taman GPRS-laitteen alaisuudessa. Luodaan BT-yhteydet.");
		BTInit();
	pass;
	if GPRSMode:
		pass;
		# synkronoidaan kello loopin aluksi
		if synkronoidaanKello:
			kellonSynkronointiLooppi();
	if ethernetMode:
		debug("Kommunikaatio-ohjelmistoa ei ole tarpeen alustaa, silla kaytetaan olemassaolevaa internet-yhteytta.")
		if synkronoidaanKello:
			kellonSynkronointiLooppi();
		

# ------------------- MITTAUSTEN LUKEMINEN -----------------------------
def lueReleTieto():
	releTieto=GPIOhallinta.lueReleTieto1();
	releTietoInt=booleanToInt(releTieto);
	return releTietoInt; # 1=rele johtaa

#########################################################################################################

# ------------------- viestit palvelimelle -----------------------------

def luoSynkViesti(syyData=0):
	# {'aikasynk': {'laiteaika': 1539083167037}} - HUOM: millisekunteina; TP:n aika on kehyksessa millisekunteina
		
	viesti={}
	aikaleimaNyt = int(round(time.time() * 1000));
	aikasynkViesti={"laiteaika": aikaleimaNyt}
	
	if syyData >0: # 0 = ajastettu saannollinen synkrointi - default
		aikasynkViesti={"laiteaika": aikaleimaNyt, "syy": syyData}
	
	viesti["aikasynk"] = aikasynkViesti
	
	# viesti = {"aikasynk": {"laiteaika": aikaleimaNyt}}; # toimiva rakenne
	# viesti = {"aikasynk": {"laiteaika": aikaleimaNyt, "syy":1}}; # Syy on valinnainen kentta
	
	# paluuViesti=sendToServer(str(viesti)); # paluuViesti voi olla esim. katkoviesti tai kellojen erotus
	return viesti;
	
def luoLyhytMittausviesti(kokoMittausviesti): # vanha rakenne lyhyelle viestille. Ei kaytossa nyt.
	global mittauksiaTallennetaan;
	keskiarvo1=0;
	keskiarvo2=0;
	keskiarvo3=0;
	kertyma1=0.0;
	kertyma2=0.0;
	kertyma3=0.0;
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
		
	pakattuLyhytViesti=viestinpurku.pakkaa_viesti({"mittaukset": tulosMittaukset, "pituusMinuutteina": kommunikaatioValinPituus});
	lyhytViesti=pakattuLyhytViesti
	## kommunikaatioValinPituus = mittauksiaTallennetaan * mittausJaksonPituus
	return lyhytViesti;


def luoLyhyetMittausviestit(kokoMittausviesti): # jaetaan koko viesti 2 osaan - jai tarpeettomaksi syklimuutosten jalkeen
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


def luoLyhyetMittausviestit3(kokoMittausviesti): # jaetaan koko viesti 3 osaan - jai  tarpeettomaksi syklimuutosten jalkeen
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

def loraSendToServerInThreeParts(kokoMittausViesti): # jai tarpeettomaksi - kommunikaationopeus pyritaan ennakoimaan
	LoraDataRate=2; # turha alustus
	if (LoraDataRate<3) and ("mittaukset" in kokoMittausViesti):
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
	# Ilmaistaan valvovalle ohjelmalle, etta ohjelma on kaynnissa 
	global ohjelmanStatus;
	ohjelmanStatus+=1;
	if ohjelmanStatus>11000:
		ohjelmanStatus=ohjelmanStatus-10000
	statusJSON = {};
	statusJSON['status'] = {'koodi': ohjelmanStatus};
	debug("Ilmaistaan ohjelman olevan kaynnissa;")
	debug(statusJSON); # Kirjataan ohjelman status tiedostoon: ohjelmanTila.json --> {"status": {"koodi": 1}}	
	with open('ohjelmanTila.json', 'w') as outfile:
		json.dump(statusJSON, outfile)
	
	global mittauksiaLuettu;
	global liukuvaTeho1;
	global liukuvaTeho2;
	global liukuvaTeho3;
	global tallennuksia;

	mittauksiaLuettu=0;
	liukuvaTeho1=0.0;
	liukuvaTeho2=0.0;
	liukuvaTeho3=0.0;
	liukuvaMittauksetKestiMillisec=0;
	
	for j in range(0, mittausPurskeita): # oletus noin 5 minuutin looppi eli mittausPurskeita = 10, joista kukin 30 s
		debug("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
		debug("Mittauspurskekierros: {0} / {1}".format(j+1, mittausPurskeita))
		debug("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
					
		kaikkiOK=True;
		if LoraMode:
			kaikkiOK=hallitseIntegrity()
		if (not kaikkiOK):
			debug("On syyta epailla, etta Laird toimii virheellisesti.")

		mittaustenAlkuAika = int(round(time.time() * 1000)); # aikaleima millisekunteina
		mittauksiaLuettu +=1;
		
		# LED-vilkutus n. 3s alkaa # Asetetaan punainen LED pois paalta
		GPIOhallinta.LED3off();
		
		average1teho, average2teho, average3teho, mittausKestiMillisec = mittausMCP3008.mittausLooppi(); # luetaan 3 x 1s tehot
		
		# LED-vilkutus n. 3s loppuu # Asetetaan punainen LED takaisin paalle.
		GPIOhallinta.LED3on();
		
		#liukuvat keskiarvot
		liukuvaTeho1+=average1teho;
		liukuvaTeho2+=average2teho;
		liukuvaTeho3+=average3teho;
		liukuvaMittauksetKestiMillisec+=mittausKestiMillisec;
		debug ("Mittaus numero: " + str(mittauksiaLuettu)+" ; mittausKestiMillisec: " + str(mittausKestiMillisec)+" ms ; average1teho: " + str(average1teho)+" W ; liukuvaTeho1: " +str(liukuvaTeho1)+" W.");
		
		# eri kierroksilla tehdaan eri asioita. Mikali kommunikaatiojaksoja on varmasti enemman, voidaan jaotella tarkemmin.
		  # Nyt oletuksena vahintaan 2 mittauskierrosta (esim. 2 x 30 sek.)
		  # eka kierros --> viedaan komento BT-laitteelle
		  # toiseksi viimeinen kierros --> haetaan mittausdata BT-laitteelta
		  # viimeinen kierros --> jatetaan tauko valiin, koska saatetaan lahettaa dataa palvelimelle
		debug("Tarkastetaan katkotietokanta ja luodaan katkosaikeet, seuraavan minuutin aikana alkaville katkoille.")
		katkoSQL.tarkastaKatkotaulu(70); # Tarkastetaan katkotaulusta pian alkavat katkot. Voidaan ajaa toistuvasti (ilman tuplia), silla vain ei-aktiiviset katkot kaynnistetaan.

		if mittauksiaLuettu==1: # eka kierros  # ekalla kierroksella toimitetaan palvelimen viestit BT-laitteille
			debug("Mittauskierros - 1 mittaus luettu.")
			# katkoSQL.tarkastaKatkotaulu(360); # Aiemmin katkosaikeet 5 minuutiksi tulevaisuuteen. Nyt 1 min.
			global vilkutetaanPunaistaLedia;
			if vilkutetaanPunaistaLedia:
				GPIOhallinta.LED3vilkutus(vilkutuskertoja=2, vilkutusnopeus=0.5); # vilkutuskertoja=20, vilkutusnopeus=0.5)
				vilkutetaanPunaistaLedia=False;
			if BTmode:
				# debug("Eka mittauskierros. Lahetetaan BT-laitteen kaskyt, jos orjalaitteita.")
				debug("Ekalla kierroksella toimitetaan palvelimen viestit BT-laitteille");
				global viestiBTlaitteelle1; global viestiBTlaitteelle2; global viestiBTlaitteelle3; global viestiBTlaitteelle4;
				global vastausBTlaitteelta1; global vastausBTlaitteelta2; global vastausBTlaitteelta3; global vastausBTlaitteelta4;

				for laitenumero in range(0, BTlaite_lkm):
					laitenumero+=1;
					
					debug("Lahetettiin viesti BT-laitteelle numero: {0} ja saatiin vastaus: {1}".format(laitenumero, kytkinlaitteenVastaus))
					if laitenumero==1:
						 vastausBTlaitteelta1=BTcom.BTCentralSendToPeripheral(viestiBTlaitteelle1, laitenumero); 
					if laitenumero==2:
						vastausBTlaitteelta2=BTcom.BTCentralSendToPeripheral(viestiBTlaitteelle2, laitenumero); 
					if laitenumero==3:
						vastausBTlaitteelta3=BTcom.BTCentralSendToPeripheral(viestiBTlaitteelle3, laitenumero); 
					if laitenumero==4:
						vastausBTlaitteelta4=BTcom.BTCentralSendToPeripheral(viestiBTlaitteelle4, laitenumero);
				debug("BT-laitteiden vastausviestit lahetetetaan myohemmin palvelimelle, jos ne sisaltavat mittausdataa.")
				viestiBTlaitteelle1=""; viestiBTlaitteelle2=""; viestiBTlaitteelle3=""; viestiBTlaitteelle4=""; # Viestit lahetetty eteenpain.
				# debug("Odotellaan mahdollisesti viela loput 30 sekuntia taman BT:n IF-lausekkeen ulkopuolella.")
			pass;
			
		if mittauksiaLuettu==(mittausPurskeita-1): # toiseksi viimeisella tauolla haetaan BT-laitteen mittaukset
			# luetaan BT-laitteen tiedot viimeista edellisella mittauskierroksella
			if BTmode:
				debug("luetaan BT-laitteen tiedot - viimeista edellisella mittauskierroksella")
				# global viestiBTlaitteelle1; global viestiBTlaitteelle2; global viestiBTlaitteelle3; global viestiBTlaitteelle4;
				# global vastausBTlaitteelta1; global vastausBTlaitteelta2; global vastausBTlaitteelta3; global vastausBTlaitteelta4;
				
				for laitenumero in range(0, BTlaite_lkm):
					laitenumero+=1;
					
					debug("Lahetettiin viesti BT-laitteelle numero: {0} ja saatiin vastaus: {1}".format(laitenumero, kytkinlaitteenVastaus))
					if laitenumero==1:
						vastausBTlaitteelta1uusi=BTcom.BTCentralSendToPeripheral(viestiBTlaitteelle1, laitenumero);
						vastausBTlaitteelta1+=vastausBTlaitteelta1uusi; # ketjutetaan vastaukset perakkain. Kaytannossa toinen vastaus on aina tyhja.
					if laitenumero==2:
						vastausBTlaitteelta2uusi=BTcom.BTCentralSendToPeripheral(viestiBTlaitteelle2, laitenumero); 
						vastausBTlaitteelta2+=vastausBTlaitteelta2uusi;
					if laitenumero==3:
						vastausBTlaitteelta3uusi=BTcom.BTCentralSendToPeripheral(viestiBTlaitteelle3, laitenumero); 
						vastausBTlaitteelta3+=vastausBTlaitteelta3uusi;
					if laitenumero==4:
						vastausBTlaitteelta4uusi=BTcom.BTCentralSendToPeripheral(viestiBTlaitteelle4, laitenumero);
						vastausBTlaitteelta4+=vastausBTlaitteelta4uusi;
						
				debug("BT-laitteiden vastausviestit lahetetetaan myohemmin palvelimelle, jos ne sisaltavat mittausdataa.")
				BTcom.BTCentralSendToPeripheral("Palauta mittaukset",1)
			pass;
		if mittauksiaLuettu==mittausPurskeita: # jatetaan viimeinen tauko valiin
			debug("Viimeinen mittauskierros: "+str(mittauksiaLuettu)+" --> tauko jaa valiin.  Poistutaan mittausKierroksesta.");
			# debug("Luettiin viimeinen mittaus 5 minsan keskiarvoon. Jatetaan tauko valiin.")
		
		if mittauksiaLuettu<mittausPurskeita: # jatetaan viimeinen tauko valiin
			mittaustenLoppuAika = int(round((time.time() * 1000)+syklinPituusKorjaus)); # aikaleima millisekunteina + arvioitu loopin vaihdon kesto
			mittaustenKesto = mittaustenLoppuAika - mittaustenAlkuAika; # ms
			# debug ("Mittauksia luettu :" +str(mittauksiaLuettu));
			mittausTauko=purskeidenLukemisVali-(float(mittaustenKesto)/1000); # 30 sekuntia - mittauksiin kaytetty aika
			if fakeTimeSpeedUp:
				mittausTauko=0.1 # testivaiheessa ohitetaan odotus
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
		debug("yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy")
		debug("Mittauskierrosten ketju: {0} / {1}".format(i+1,mittauksiaTallennetaanInput))
		debug("yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy")
		tallennuksia+=1;
		aikaleimaNyt = int(round(time.time() * 1000)) # timestamp in millisec
		aikaleimaNytSekunteina=int(round(aikaleimaNyt/1000.0));
		# lasketaan 5 min tehokeskiarvot
		keskiArvoTeho1, keskiArvoTeho2, keskiArvoTeho3,liukuvaMittauksetKestiMillisec = mittausKierros(mittausPurskeita);
		releenAsento=lueReleTieto(); # True = rele johtaa
		aikaleimaMittauskierroksenLopussa = int(round(time.time() * 1000)) # timestamp in millisec
		aikaleimaMittauskierroksenLopussaSekunteina=int(round(aikaleimaMittauskierroksenLopussa/1000.0));
		mittauksetListana.append((keskiArvoTeho1, keskiArvoTeho2, keskiArvoTeho3, releenAsento))
			
		debug ("5 min ka teho: liukuvaTeho1/mittausPurskeita = " + str(keskiArvoTeho1));
		# OLD: mittauksetListana.append((omaLaiteID, aikaleimaNytSekunteina, keskiArvoTeho1, keskiArvoTeho2, keskiArvoTeho3, releenAsento))
		liukuvaKetjuKestiMillisec+=liukuvaMittauksetKestiMillisec; # ajastuksen apumuuttuja
		if saveData: # tarpeen vain kehitysvaiheessa # poista kaytosta lopullisessa laitteessa 
			mittausTietoString=str(aikaleimaNytSekunteina) + "," +str(keskiArvoTeho1) + "," +str(keskiArvoTeho2) + "," +str(keskiArvoTeho3) + "," + str(releenAsento) + "\n";
			payloadCSVold=payloadCSV;  
			payloadCSV=payloadCSVold+mittausTietoString; 
			#kirjataan tiedostoon	
			pass
		aikaleimaLopussa = int(round(time.time() * 1000)) # timestamp in millisec
		debug("5 minuutin keskiarvoja on nyt kirjattu: " +str(tallennuksia)+" kpl. Keskiarvoja kirjataan, ennen lahettamista: "+str(mittauksiaTallennetaanInput)+" kpl.")
		KetjuKestiSec=int(round((aikaleimaLopussa-aikaleimaNyt)/1000.0));
		debug("Koko 30min koko ketju kesti: " + str(KetjuKestiSec)+" s.")	
		if tallennuksia < mittauksiaTallennetaanInput: # tauko, jos turhaa aikaa mittausten valissa eika viimeinen mittaus	
			nukutaan=mittausKierroksenKesto-KetjuKestiSec; # 5 minuuttiin aikaa 5 * 60 = 300
			debug("---------------------- nukutaan mittausKierrostenKetjussa: " + str(nukutaan))
			if nukutaan>0:
				if fakeTimeSpeedUp:
					nukutaan=0.1; # TODO poista - ei jaksa odottaa testivaiheessa
					debug("Fake time SpeedUp --> nukutaan mittausKierrostenKetjussa: " + str(nukutaan))
				time.sleep(nukutaan)
			debug("Ketjun lopuksi nukuttiin: " + str(nukutaan)+" s.")
			pass
	
	if saveData: # Testausvaiheessa kirjataan mittausdata talteen
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
	kokoMittausViesti["aika"] = aikaleimaMittauskierroksenLopussaSekunteina;
	#kokoMittausViesti["pituusMinuutteina"] = 5;
	
	if lahetettavanDatanPituusMinuutteina!=5:
		kokoMittausViesti["pituusMinuutteina"] = lahetettavanDatanPituusMinuutteina;
		
	debug("Ketjun mittauksien toteuttaminen kesti: " + str(liukuvaKetjuKestiMillisec)+" ms.")
	debug("Luotiin palvelimelle lahetettava viesti: {}".format(kokoMittausViesti))
	
	return (kokoMittausViesti, liukuvaKetjuKestiMillisec);

	
####################################################################################
# real COM - looppi
####################################################################################
def kommunikaatioLooppi(omaLaiteID, synkronointiLooppi=2): # 0 = ei synk vain mitt. , 1 = synk ja mittaus, 2 = vain synk
	synkronointiEpaonnistui=False;
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
		if LoraDataRate<3 and mittauksiaTallennetaan>2: # Koska voidaan lahettaa vain pienia viesteja, rajataan viestikoko enintaan 2 mittauksen kokoiseksi
			mittauksiaTallennetaan=2; # 2 x 5 minuutin mittauskierros eli tallennetaan 2 keskiarvoa ja sitten sendToServer
		if LoraDataRate>=3 and mittauksiaTallennetaan>6: # Voidaan lahettaa isompia viesteja. Rajataan viestikoko enintaan 6 mittauksen kokoiseksi
			mittauksiaTallennetaan=6; # 6 x 5 minuutin mittauskierros ja sendToServer
	
	# LOOPIN TOIMINNALLISUUDEN VALINTA
	if (synkronointiLooppi<2): # tilat 0 ja 1 mittaavat tehot
		kokoMittausViesti, liukuvaKetjuKestiMillisec=mittausKierrostenKetju(omaLaiteID, mittauksiaTallennetaan, mittausPurskeita, mittausKierroksenKestoSekunteina); # mittausviesti on luotu
		# debug("Kommunikaatiolooppi sending to server") # lahetetaan mittausviesti palvelimelle
		# kaikissa moodeissa yhteiset toiminnot
		paluuViesti=sendToServer(kokoMittausViesti); # viesti lahetettiin palvelimelle ja saatiin paluuviesti
			
	if (synkronointiLooppi==1): # tila 1 synkronoi ja mittaa, 2 synkronoi
		# Kasitellaan ensimmainen paluuviesti
		paluuViestiDictPala=parseServerMessage(paluuViesti);  # kasitellaan ensimmainen paluuviesti palvelimelta
		palvelimenAikaSynkVastaus={}
		if paluuViestiDictPala:
			palvelimenAikaSynkVastaus=handleServerReply(paluuViestiDictPala);
		if (not paluuViestiDictPala):
			debug("Ei paluuviestia palvelimelta");
		paluuViesti=sendSynkToServer(0); # viesti lahetettiin palvelimelle ja saatiin paluuviesti
	
	if (synkronointiLooppi==2): # eka kierros, ohitetaan viiveet
		liukuvaKetjuKestiMillisec=mittauksiaTallennetaan*mittauksiaTallennetaan*mittausKierroksenKestoSekunteina-10; # ohitetaan loopin ajantasaukset
		paluuViesti=sendSynkToServer(1); # lahetetaan Raspin kellonaika synkronointiviestina (mittausviestin sijaan)
									
	paluuViestiDictPala=parseServerMessage(paluuViesti);  # kasitellaan paluuviesti palvelimelta		
	palvelimenAikaSynkVastaus={}
	if paluuViestiDictPala:
		palvelimenAikaSynkVastaus=handleServerReply(paluuViestiDictPala);
		debug("handleServerReply palautti palvelimenAikaSynkVastaus: {0}".format(palvelimenAikaSynkVastaus));
	if not paluuViestiDictPala:
		debug("Ei paluuviestia palvelimelta");
	
	# yksi mittaus/palvelin-sykli on suoritettu. Odotellaan ehka hetki.
	if paivitaSofta: # Asennetaan paivitys, jos on kokonaisuudessaan ladattu asennettavaksi uusi ehja smartBasic-ohjelma.
		updateSmartBasic();
			
	################## Loopin kesto kiinnittaminen tasan 10 tai 30 minuuttiin ##########################
	loopinLoppuAika = int(round(time.time() * 1000)); # aikaleima millisekunteina
	loopinKesto = loopinLoppuAika - loopinAlkuAika; # aika millisekunteina - po noin 10 tai 30 min eli mittauksiaTallennetaan * 5 min
	debug("Loopin kesto oli: " +str(loopinKesto/1000.0) + " sekuntia. ") 
	
	if (synkronointiLooppi==2):
		debug("Ohitetaan viiveet, silla ajetaan vain synkronointilooppi.");
		loopinKesto=((mittauksiaTallennetaan*300)-0.001)*1000.0;	
		debug("Huijattu loopin kesto: " +str(loopinKesto/1000.0) + " sekuntia. ")  	
		
	if fakeTimeSpeedUp: # huijataan, etta looppi kesti halutun ajan
		loopinKesto=((mittauksiaTallennetaan*300)-0.001)*1000.0;	
		debug("Huijattu loopin kesto: " +str(loopinKesto/1000.0) + " sekuntia. ")  	
		
	looppiOliLiianNopea = (mittauksiaTallennetaan * mittausKierroksenKestoMinuutteina *60*1000) - (loopinKesto); # ms
	debug("------------------------------------------------------------------------- Odotellaan, etta : " +str(mittauksiaTallennetaan*mittausKierroksenKestoMinuutteina)+ " minuuttia (oletus 10 tai 30) tulee tayteen eli odotetaan: " + str(looppiOliLiianNopea/1000) + " s")
	
	if odoteltuLiikaaAiemmin>300: # jos yli 5 minsaa jaljessa poistetaan kokonaiset 5 minuutin jaksot, joita ei saada kirittya kiinni
		odoteltuLiikaaAiemmin=odoteltuLiikaaAiemmin%300; # odoteltuLiikaaAiemmin MODULO 300
	seuraavaanLooppiinAikaa = looppiOliLiianNopea - odoteltuLiikaaAiemmin 
	if fakeTimeSpeedUp:
		seuraavaanLooppiinAikaa=1000;
	
	if seuraavaanLooppiinAikaa>0:
		time.sleep(seuraavaanLooppiinAikaa/1000.0);
		odoteltuLiikaaAiemmin=0;
	else:
		odoteltuLiikaaAiemmin=0-(seuraavaanLooppiinAikaa/1000.0); # s
	debug("Paaloopin ajastuksen lopputasaus. Looppi oli liian nopea: "+str(looppiOliLiianNopea)+" ms ; Odoteltiin hetki: "+str(seuraavaanLooppiinAikaa) + " ms ; odoteltuLiikaaAiemmin: " + str(odoteltuLiikaaAiemmin))
	debug("Loopin loputtua aikasynk. Muuten tahdistus menee pieleen.")
	erotus=None;
	if "erotus" in palvelimenAikaSynkVastaus:
		debug("Loydettiin erotus palvelimenAikaSynkVastauksesta: {0}".format(palvelimenAikaSynkVastaus));
		erotus=palvelimenAikaSynkVastaus['erotus'];
		doTimeSynk(erotus); # Raspi muuttaa omaa kelloaan
		synkronointiEpaonnistui=False;
		# doTimeSynkDemo(erotus); # testikomento, joka vain simuloi kellon synkronoinnin
	if (synkronointiLooppi==2) and (erotus==None):
		synkronointiEpaonnistui=True;
	return synkronointiEpaonnistui;
	
# Orjalaitteella sendToServer --> saveForServer()
def saveForServer(kokoMittausViesti):
	paluuViesti=""
	# SAVE BTSlaveViestiPalvelimelle.txt
	debug("Tallennetaan mittaustulokset tiedostoon - palvelimelle lahetettavaksi - BTSlaveViestiPalvelimelle.txt.")
	overWriteData("BTSlaveViestiPalvelimelle.txt",kokoMittausViesti)
	
	# READ BTSlaveViestiPalvelimelta.txt
	debug("Luetaan palvelimen viesti tiedostosta - BTSlaveViestiPalvelimelta.txt.")
	paluuViesti=readData("BTSlaveViestiPalvelimelta.txt")
	return paluuViesti;

def tarkistaOrjalaitteenKello():
	korjataanKelloa=False;
	erotusViesti=0
	# READ BTSlaveViestiPalvelimelta.txt
	debug("Luetaan palvelimen viesti tiedostosta - BTSlaveViestiPalvelimelta.txt.")
	erotusViesti=readData("BTSlaveKellonSiirto.txt")
	overWriteData("BTSlaveKellonSiirto.txt", "Nollattu kellonkorjausviesti."); # Varmistetaan, etta korjataan kelloa vain kerran yhdella erotuksella.
	try:
		erotusOnInteger=isinstance(erotusViesti, int)
		if erotusOnInteger:
			if erotusViesti!=0:
				korjataanKelloa=True;
			else:
				debug("Ei annettu uutta kellonaikaa");
		if korjataanKelloa:
			debug("Loydettiin erotus ohjauslaitteen vastauksesta: {0}".format(erotusViesti));
			doTimeSynk(erotusViesti); # Raspi muuttaa omaa kelloaan
	except:
		debug("Jokin meni pieleen kellonaikaa asettaessa.")
		korjataanKelloa=False;
	return korjataanKelloa;

####### ORJALAITTEEN LOOPPI #######
def orjaLaitteenKommunikaatioLooppi(omaLaiteID):
	kellonSynkronointeja=0;

	debug("------------------------- orjalaitteen mittaus- ja kommunikaatiolooppi alkaa ---------------------------------------------")
	loopinAlkuAika = int(round(time.time() * 1000)); # aikaleima millisekunteina
	
	# global paivitaSofta; # True, jos on ladattu asennettavaksi uusi smartBasic-ohjelma		
	global mittauksiaTallennetaan;
	global odoteltuLiikaaAiemmin;
	
	lyhytMittausviesti="null"
	paluuViestiDictPala={};
	paluuViesti="null"
	
	if (kellonSynkronointeja==0):
		debug("Orjalaite on kaynnistetty, eika kelloa ole viela synkronoitu. Ei kirjata mittauksia, eika luoda keskeytyksia. ")
		time.sleep(5); # Odotellaan 5 sekuntia ja koitetaan uudelleen.
		tyhjaViesti="Anna kellonaika, niin mittaan."
		# Tarkastetaan onko kellosynk-viesteja
		kellonOnAsetettu=tarkistaOrjalaitteenKello()
		if kellonOnAsetettu:
			# Jos paluuviestissa on tieto siita, etta kello on asetettu oikeaan aikaan, niin: 
			kellonSynkronointeja+=1;
			pass;
			
	# LOOPIN TOIMINNALLISUUDEN VALINTA
	if (kellonSynkronointeja>0):
		debug("Kello on asetettu oikeaan aikaan, joten ajetaan mittauslooppi.")
		kokoMittausViesti, liukuvaKetjuKestiMillisec=mittausKierrostenKetju(omaLaiteID, mittauksiaTallennetaan, mittausPurskeita, mittausKierroksenKestoSekunteina); # mittausviesti on luotu
		# debug("Kommunikaatiolooppi sending to server") # lahetetaan mittausviesti palvelimelle
		# kaikissa moodeissa yhteiset toiminnot
		paluuViesti=saveForServer(kokoMittausViesti); # viesti lahetettiin palvelimelle ja saatiin paluuviesti
	
	paluuViestiDictPala=parseServerMessage(paluuViesti);  # kasitellaan ensimmainen paluuviesti palvelimelta
	palvelimenAikaSynkVastaus={}
	if paluuViestiDictPala:
		palvelimenAikaSynkVastaus=handleServerReply(paluuViestiDictPala);
		debug("handleServerReply palautti palvelimenAikaSynkVastaus: {0}".format(palvelimenAikaSynkVastaus));
	if not paluuViestiDictPala:
		debug("Ei paluuviestia palvelimelta");
	
	# yksi mittaus/palvelin-sykli on suoritettu. Odotellaan ehka hetki.
	
	# if paivitaSofta: # Asennetaan paivitys, jos on kokonaisuudessaan ladattu asennettavaksi uusi ehja smartBasic-ohjelma.
	#	updateSmartBasic();
			
	################## Loopin kesto kiinnittaminen tasan 10 tai 30 minuuttiin ##########################
	loopinLoppuAika = int(round(time.time() * 1000)); # aikaleima millisekunteina
	loopinKesto = loopinLoppuAika - loopinAlkuAika; # aika millisekunteina - po noin 10 tai 30 min eli mittauksiaTallennetaan * 5 min
	debug("Loopin kesto oli: " +str(loopinKesto/1000) + " sekuntia. ") 
		
	looppiOliLiianNopea = (mittauksiaTallennetaan * mittausKierroksenKestoMinuutteina *60*1000) - (loopinKesto); # ms
	debug("------------------------------------------------------------------------- Odotellaan, etta : " +str(mittauksiaTallennetaan*mittausKierroksenKestoMinuutteina)+ " minuuttia (oletus 10 tai 30) tulee tayteen eli odotetaan: " + str(looppiOliLiianNopea/1000) + " s")
	
	if odoteltuLiikaaAiemmin>300: # jos yli 5 minsaa jaljessa poistetaan kokonaiset 5 minuutin jaksot, joita ei saada kirittya kiinni
		odoteltuLiikaaAiemmin=odoteltuLiikaaAiemmin%300; # odoteltuLiikaaAiemmin MODULO 300
	seuraavaanLooppiinAikaa = looppiOliLiianNopea - odoteltuLiikaaAiemmin 
	
	if fakeTimeSpeedUp:
		seuraavaanLooppiinAikaa=100;
	
	if seuraavaanLooppiinAikaa>0:
		time.sleep(seuraavaanLooppiinAikaa/1000.0);
		odoteltuLiikaaAiemmin=0;
	else:
		odoteltuLiikaaAiemmin=0-(seuraavaanLooppiinAikaa/1000.0); # s
	debug("Paaloopin ajastuksen lopputasaus. Looppi oli liian nopea: "+str(looppiOliLiianNopea)+" ms ; Odoteltiin hetki: "+str(seuraavaanLooppiinAikaa) + " ms ; odoteltuLiikaaAiemmin: " + str(odoteltuLiikaaAiemmin))
	
	debug("Loopin loputtua aikasynk. Muuten tahdistus menee pieleen.")
	erotus=None;
	# luetaan Erotus tiedostosta.
	tarkistaOrjalaitteenKello()
	return;
####### ORJALAITTEEN LOOPPI #######

def BTslaveStartProsedure():
	# Nollataan tiedostot.
	overWriteData("BTSlaveKellonSiirto.txt", "Nollattu kellonkorjausviesti."); # Varmistetaan, etta korjataan kelloa vain kerran yhdella erotuksella.
	# overWriteData("BTSlaveViestiPalvelimelta.txt", "Nollattu palvelimen paluuviesti."); # Varmistetaan, etta korjataan kelloa vain kerran yhdella erotuksella.
	overWriteData("BTSlaveViestiPalvelimelle.txt", "Nollattu palvelimelle lahteva viesti."); # Varmistetaan, etta korjataan kelloa vain kerran yhdella erotuksella.

def startRaspiProsedure():	
	debug('Clearing data files\n')
	clearDataFile("datafile.csv")
	# poistetaan lukot BT-versiossa
	if BTslaveMode:
		BTslaveStartProsedure()

def closeRaspiProsedure():
	# Tarpeen vain testauksessa
	debug("Suljetaan ohjelma, jota ennen vapautetaan IO ja suljetaan tietokanta")
	# Vapautetaan IO
	GPIOhallinta.vapautaIO();
	# vapautetaan SQL-tietokanta
	katkoSQL.suljeTietokanta();
	
#######################################################################################
# ------------------------------- MAIN alustukset ----------------------------------- #
#######################################################################################

startRaspiProsedure(); # Tarkistetaan asetukset ja tiedostot, alustetaan mittauslaitteisto yms.

GPIOhallinta.alustaIO(); # Alustetaan IO

# alustetaan tietokanta
katkoSQL.avaaTietokanta(); # avaa tietokanta ja luo jos puuttuu
katkoSQL.luoKatkotaulu();  # luo katkotaulu, jos puuttuu

################################################################################################################################
################################################################################################################################
if automaattinenNollaVirranKalibrointi: # Nollavirran kalibrointimittaus 
	debug("Ajetaan MCP3008 virran nollatason kalibrointimittaukset.")
	# tiedostoon nollavirranraakamittaukset.csv tallennetaan mittausten tiedot: mittaussyklin nro; mittausten lukumaara; vaiheen1 virta-mittausten keskiarvo, vaiheen2 virta-mittausten keskiarvo, vaiheen3 virta-mittausten keskiarvo, mittausjakson kesto
	mittausMCP3008.nollavirranKalibrointimittaus(3, 5*mittauksiaSekunnissa); # (keskiarvojaKirjataan=5,mittauksiaKalibroinnissa=1830)
	
	# Jannitteen kalibrointimittaus # tiedostoon janniteraakamittaukset.csv tallennetaan mittausten tiedot: mittaussyklin nro; mittausten lukumaara; mittausten keskiarvo
	mittausMCP3008.jannitemittausKalibrointiTiedostoon(2, 1*mittauksiaSekunnissa); # (keskiarvojaKirjataan=5, mittauksiaKeskiarvoon=1830) 


################################################################################################################################
################################################################################################################################

# INIT
alustaKommunikaatioLaite() # Otetaan laite fyysisesti kayttoon ja valmistellaan softa - ei luoda yhteytta ulkomaailmaan
randomTaukoKatkonJalkeen(); # random delay 0-10 min tai 0-30 min
alustaKommunikaatioSofta(True); # Alustetaan kommunikaatio, luodaan yhteys. True - synkronoidaan kello

# Tarkistetaan laitteen looginen toiminta

###############################################################################
# ----------------------- MAIN LOOPPI -----------------------------------------
###############################################################################
kerrotaanAika=True; # Voidaan poistaa lopullisesta ohjelmistosta.
if kerrotaanAika:
	aikaleimaIn = int(round(time.time())); # timestamp in s
	kelloJaPaiva=datetime.datetime.fromtimestamp(
		int(aikaleimaIn)
		).strftime('%Y-%m-%d %H:%M:%S');
	debug("\n -------------------------- Paaohjelma kaynnistyi, kun aikaleima on: {0} - pwm ja time: {1} -------------------------- \n".format(aikaleimaIn, kelloJaPaiva));

looppiLaskuri=0

############################### PAAOHJELMAN IKUISET LOOPIT ###############################

# Jos kyseessa on BT-orjalaite, niin taysin oma looppi ajoon.
if BTslaveMode:
	debug("BT-orjalaitteen oma looppi alkaa.")
	while True:
		orjaLaitteenKommunikaatioLooppi(omaLaiteID)
	
while True:
	kommunikaatioLooppiAjettu=False;
	
	looppiLaskuri+=1
	if looppiLaskuri==1: # vain synkronoidaan kello
		# kommunikaatioLooppi(omaLaiteID, 2); # ------------- Ajetaan mittaus/palvelin-sykli - MITTAUSLOOPPI - 12 x 5 min
		# kommunikaatioLooppiAjettu=True;
		debug("Laite on juuri kaynnistetty ja synkronointiviesti on lahetetty kommunikaatiosoftaa alustettaessa."); # Ensimmainen kierros.
	
	# tahan valiin tulee tunnin valein tehtavat tarkastukset tms.
	if (looppiLaskuri%kierroksiaTunnissa)==0: # modulo: luku % jakaja = jakojaannos
		debug("Laite on ollut kaynnissa tasatunnin.");
		pass;
	
	# tahan valiin tulee vuorokauden valein tehtavat tarkastukset tms.
	if (looppiLaskuri%kierroksiaVuorokaudessa)==0:
		sendFailedCountToday=0; # nollataan globaali kommunikaatiovirheiden laskuri
		debug("Laite on ollut kaynnissa vuorokauden monikerran.");
		synkronointiEpaonnistui=kommunikaatioLooppi(omaLaiteID, 1); # synkronoidaan kello
		kommunikaatioLooppiAjettu=True;
	pass;
	
	if (not kommunikaatioLooppiAjettu):
		synkronointiEpaonnistui=kommunikaatioLooppi(omaLaiteID, 0); # ------------- Ajetaan mittaus/palvelin-sykli - MITTAUSLOOPPI - 12 x 5 min
	
	if looppiLaskuri>kierroksiaKuukaudessa+4: # ei nollata laskuria, niin voidaan ensimmaisilla kierroksilla toimia eri tavoin
		looppiLaskuri=looppiLaskuri-kierroksiaKuukaudessa
	pass;
	
