#!/usr/bin/env python
# -*- coding: utf-8 -*-

# mittausMCP3008.py – Current and voltage measurements with the MCP3008 AD converter
# - Reading the current and voltage measurements via the GPIO SPI bus to the MCP3008 AD converter. The program component defines measurement reading, measurement calculations, calibration the measurements, etc. 
# mittausMCP3008.py – virta- ja jannitemittaukset MCP3008 AD-muuntimella
# - Luetaan GPIO:n SPI-vaylan kautta MCP3008-AD-muuntimelle tulevat virta- ja jannitemittaukset. Ohjelmakomponentissa maaritellaan mittauksen lukeminen, mittauksen laskentatoimenpiteet, kalibrointimittaukset jne.

import json;
with open('asetukset.json') as json_general_settings_file:
	asetus	= json.load(json_general_settings_file)
with open('kommunikaatio.json') as json_com_settings_file:
	kommunikaatioasetus	= json.load(json_com_settings_file)
with open('testiasetukset.json') as json_testi_settings_file:
	testiasetus	= json.load(json_testi_settings_file)
with open('kalibrointi.json') as json_testi_settings_file:
	kalibrointiasetus = json.load(json_testi_settings_file)
with open('toimintatila.json') as json_testi_settings_file:
	toimintatila = json.load(json_testi_settings_file)
	
BTmode = kommunikaatioasetus['com']['BTmode'];   # True, jos BT-laite GPRS:n alaisuudessa

## Testiasetus. Maaritellaan laitekokoonpano:
JanniteKanavaOnKolme=False; # Oletus Lora- tai BT-laitteen alkuperainen IO-asettelu
GPRSMode = kommunikaatioasetus['com']['GPRSMode']; # True; # 1, jos GPRS-COMM-laite
ethernetMode = kommunikaatioasetus['com']['ethernetMode'];		# True, jos kaytetaan laitteeseen valmiiksi luotua ethernet-yhteyttaa
# JanniteKanavaOnKolme=True; # IO-korjattu GPRS-laitteisiin. True, kun GPRS-laite. False, muulloin.

if GPRSMode or ethernetMode: # HUOM! Poista tama, jos IO-maarittely noudattaa kytkentakaavioita.
	JanniteKanavaOnKolme=True
## Testiasetus. Loppuu.

# test settings;
debugON=testiasetus['test']['debugON'];# True; # kun 1, niin ei nayteta debug-funktion viesteja

def debug(data): # Komento, jolla annetaan palautetta johonkin kanavaan. Nyt tulostetaan data terminaaliin. Voidaan asettaa keskitetysti pois paalta.
	if debugON:
		print (str(data));

saveData=testiasetus['test']['saveData']; #True
naytaVirtaMittaus=True # tulostatetaan virtamittaustulokset nayttoon


# uudetNollavirranArvotKayttoon=testiasetus['test']['uudetNollavirranArvotKayttoon']; # janniteOnTuhat=False; # Saadaan virtamittaukset tehojen paikalla
# uudetNollavirranArvotKayttoon=True;


global kanavan1Keskiarvo; global kanavan2Keskiarvo; global kanavan3Keskiarvo;
kanavan1Keskiarvo=kalibrointiasetus['kalibrointi']['kanavan1Keskiarvo'];
kanavan2Keskiarvo=kalibrointiasetus['kalibrointi']['kanavan2Keskiarvo'];
kanavan3Keskiarvo=kalibrointiasetus['kalibrointi']['kanavan3Keskiarvo'];
automaattinenNollaVirranKalibrointi=kalibrointiasetus['kalibrointi']['automaattinenNollaVirranKalibrointi'];

ChannelAverage=kanavan1Keskiarvo; # ChannelAverage=513.5 # 513.5 - nollavirta 5.9.2018 # 513 kalibrointi kotona 22.8.2018; 513.5 valittu 21.08.2018 minimoimalla nollavirralla; 511 # (po. 511.5) - testit (2901_2018): 505, 509, 510, 508, 508

# kanavan nollavirran mittaustulos
virtaSkaalausKerroin=kalibrointiasetus['kalibrointi']['virtaSkaalausKerroin']; # virtaSkaalausKerroin=0.0549; #  kalibrointi 15.11.2018 

janniteSkaalausKerroin=kalibrointiasetus['kalibrointi']['janniteSkaalausKerroin']; # janniteSkaalausKerroin=0.2546635; #  kalibrointi 15.11.2018 # jannitekalibrointisuoran kulmakerroin
janniteNollataso=kalibrointiasetus['kalibrointi']['janniteNollataso']; # janniteNollataso=65.645 # kalibrointi 15.11.2018 # Jannite, kun AD-muunnin antaa arvon nolla.

# Asetukset laitteen kalibrointitilanteisiin:
kalibroidaanJannite=toimintatila['toimintatila']['kalibroidaanJannite']; # true, kun kalibroidaan jannitetta. # Lahetetaan palvelimelle CH1: 10*raakajannitemittaus, CH2: 10*laskettu jannite, CH3: laskettu jannite
kalibroidaanVirta=toimintatila['toimintatila']['kalibroidaanVirta']; # true, kun kalibroidaan jannitetta # # Lahetetaan palvelimelle CH1: 10*laskettuvirta1, CH2: 10*laskettuvirta2, CH3: 10*laskettuvirta3
varmennetaanKalibrointi=toimintatila['toimintatila']['varmennetaanKalibrointi']; # true, kun varmennetaan kalibrointituloksia # Lahetetaan palvelimelle CH1: 10*laskettuvirta1, CH2: 10*laskettujannite, CH3: laskettu teho


virtaOnYksi=False;
vakioJannite=testiasetus['test']['vakioJannite']; # vakioJannite=False; # ohitetaan mittaus, jos True
janniteOnTuhat=testiasetus['test']['janniteOnTuhat']; # janniteOnTuhat=False; # Saadaan virtamittaukset tehojen paikalla
if kalibroidaanVirta:
	janniteOnTuhat=True;
	debug("----------------------------------------- Kalibroidaan virtaa ----------------------------------------- jannite = 1000")
if kalibroidaanJannite:
	virtaOnYksi=True;
	debug("----------------------------------------- Kalibroidaan jannitetta -------------------------------------- teho = janniteraakamittaus")

def debug(data):
	# Komento, jolla annetaan palautetta johonkin kanavaan. # xxx Clear when ready.
	# Nyt tulostetaan data UARTiin.	
	if debugON:
		print (str(data));

import GPIOhallinta;
import time;
import json;
import datetime;
import math; # sqrt
import RPi.GPIO

# RPi.GPIO.setmode(GPIO.BOARD) # 
# import Adafruit_GPIO as GPIO - Voidaan tarvittaessa muuttaa kirjastoa ---> ADAFRUIT GPIO

import Adafruit_GPIO.SPI as SPI # Hardware SPI - otetaan takaisin kayttoon
import Adafruit_MCP3008; # Tuodaan kirjasto MCP3008:n lukemiseen library.

# -------------------- IO konffaus software / Hardware SPI -----------------------
hardwareSPI=False;

if False and (not hardwareSPI): # softwareSPI:
	# Define IO - Software SPI configuration:
	# HUOM! BCM-numerointi kaytossa! Mieluummin BOARD, mutta Adafruit GPIO pakottaa BCM-numerointiin.
	CLK  = 11; # 22 # default 11	(BOARD 23)
	MISO = 9;  # 27 # default 9		(BOARD 21)
	MOSI = 10; # 17 # default 10	(BOARD 19)
	CS   = 8;  # Laite 0 SPICS0  	(BOARD 24)		
	#CS   = 7  # Laite 1 SPICS1 	(BOARD 26)
	pass;
	mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI);

if False and hardwareSPI: 
	# Hardware SPI configuration:
	SPI_PORT   = 0
	SPI_DEVICE = 0
	mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))

mcp=GPIOhallinta.maaritteleMcp();

## Test GPIO-mode
#GPIOmode = GPIO.getmode(); 
#debug("MittausMCP3008 says - GPIO-mode on nyt: " + str(GPIOmode)) # ollaanko jo BCM-modessa vai BOARD?

# -------------------- MCP3008 - IO luku ja kalibroinnnit -----------------------
# miten MCP3008 IOkanavat on kytketty
IOkanava1=0; # virtamittauskanava 1 # VIRTA releen lapi; # 0
IOkanava2=2; # virtamittauskanava 2 # 2
IOkanava3=7; # virtamittauskanava 3
IOkanava4=4; # 4 # jannitemittauskanava # JANNITE releen 1 yli;
if JanniteKanavaOnKolme:
	IOkanava4=3 # ch3 vain korjatussa GRPS-laitteessa # jannitemittauskanava # JANNITE releen 1 yli;
IOkanava5=5; # syottojannitteen valvontamittaus -kanava # Regulaattorille tuleva JANNITE / 5.
# Regulaattorille tuleva JANNITE(V)/5. Oletus noin 12V/5=2,4V (eli 745); po. min 7V/5=1,4V (eli 435)

# ----------- mittaus variables CONF these ----------
purskeidenLukemisVali=asetus['general']['purskeidenLukemisVali']; # 30s
mittausPurskeita=asetus['general']['mittausPurskeita'];  # 10 kpl 30 sekunnin mittauksia 5 minuutin keskiarvoon
mittauksiaTallennetaan=asetus['general']['mittauksiaTallennetaan'];  # 6 kpl 5 minuutin keskiarvoja tallennetaan ennen muuta toiminta

mittauksiaSekunnissa=asetus['general']['mittauksiaSekunnissa']; # mittauksiaSekunnissa = 183; # 1596 # 183 Laiteriippuvainen eli monta mittausta ehtii lukea sekunnissa

	
#########################################################################################################	
# ---------------- mittaussimulaattori ---------------------------
#########################################################################################################	

def writeData(filename,outputData):
	fileOutput = open(filename,"a");
	fileOutput.write(outputData);
	fileOutput.close();
	# usage writeData("tiedostonnimi.txt","datakirjataanfileen")

def averageList(lista):
	average=sum(lista) / float(len(lista));
	return average;

def averageListFloat(lista):
	average=(sum(lista)) / float(len(lista));
	return average;

	
def averagePowList(lista):
	averageLista=sum(lista) / float(len(lista));
	average=math.sqrt(averageLista)
	return average;

# ------------------- MITTAUSTEN LUKEMINEN   -----------------------------
def lueReleTieto():
	# releTieto=not(katkoOhjaus); # toimii, mutta vastaus annetaan integerina tilan saastamiseksi
	releTieto=GPIOhallinta.lueReleTieto1();
	return releTieto; # 1=rele johtaa

def mittaaVirtakanavat():
	value1=mcp.read_adc(IOkanava1);
	value2=mcp.read_adc(IOkanava2);
	value3=mcp.read_adc(IOkanava3);
	return (value1, value2, value3);

def poistaPoikkeamaAbs(tehoIn, kanavanKeskiarvo=513): # kalibroinnissa kaytettava virtamittauksen poikkeama nollatasosta
	tehoOut=math.fabs(tehoIn-kanavanKeskiarvo);
	return tehoOut;

def poistaPoikkeama(tehoIn, kanavanKeskiarvo=513):
	tehoOut=tehoIn-kanavanKeskiarvo;
	return tehoOut;
	
def lueKavavanArvo(IOkanava):
	value=mcp.read_adc(IOkanava);
	return (value);

def mittaaJanniteRaaka():
	value=mcp.read_adc(IOkanava4);
	return (value);

def mittaaJanniteLooppi():
	jannitemittauksia=mittauksiaSekunnissa;
	janniteMittauslista=[];
	for i in range(0, mittauksiaSekunnissa):
		value=mittaaJanniteRaaka();
		janniteMittauslista.append(value);
	mitattuJannite=averageListFloat(janniteMittauslista)
	debug("Mitattiin jannite loopissa. Saatiin raaka-arvo: {0}".format(mitattuJannite))
	return (mitattuJannite);

def laskeJannite(mittausArvo): # jannite raakamittausarvosta
	laskettuJannite=janniteNollataso+float(janniteSkaalausKerroin)*mittausArvo; # jannite kalibroitu 15.11.2018
	# PNS-menetelmalla: jannite = 0,2558724 * mittaus + 77,4579841
	# laskettuJannite=0.2898994*mittausArvo+57.1118913; # tuned
	debug("Mittausarvo: {0} - Laskettu jannite: {1}.".format(mittausArvo, laskettuJannite));
	return laskettuJannite;

def mittaaJannite():
	# Kalibrointitilanteissa ohitetaan mittaus vakioarvolla
	if vakioJannite:
		jannite=230; # Kaytetaan arvoa 230, kunnes jannitemittaus on kalibroitu
		debug("Asetetaan vakiojannite: {0}".format(jannite));
		return (jannite);
	if janniteOnTuhat:
		jannite=1000; # Saadaan virtamittaukset tehojen paikalla (helposti skaalattavana)
		return (jannite);
	
	if kalibroidaanJannite:
		(jannite,laskettuArvo)=mittaaRaakaJanniteSykli(20); # mitataan 20 sekuntia
	else:
		value=mittaaJanniteLooppi();
		jannite=laskeJannite(value);

	debug("Mitattu jannite on: " +str(jannite));
		
	return (jannite);

def mittaaRegulaattorinJannite(): # Regulaattorille tuleva JANNITE(V)/5. Oletus noin 12V/5=2,4V (eli 745); po. min 7V/5=1,4V (eli 435)
	value=mcp.read_adc(IOkanava5); # Mittaus AD: 0 - 1024 vastaa 0 - 3,3 V   # Kun Utod = 12 V, niin # Umit = Utod / 5 = 2,4 V
	regulaattorinJannite=(value)*3.3*5/1024 ; # skalaus: value / 1024 * 3,3 * 5 = Utodellinen
	# debug("Jannite mitattu: {0} ; Jannite LASKETTU: {1}".format(value, regulaattorinJannite));
	return regulaattorinJannite;
	
def regulaattorinJanniteTestit():
	janniteRaja=9;
	sallittuJannitePudotus=0.05;
	jannite1=mittaaRegulaattorinJannite();
	time.sleep(0.1)
	jannite2=mittaaRegulaattorinJannite();
	testi1=jannite1<janniteRaja; # alhainenjannite1
	testi2=jannite2<janniteRaja; # alhainenjannite2
	testi3=jannite2+sallittuJannitePudotus<jannite1; # pudonnutJannite
	return (testi1, testi2, testi3)
	
def regulaattorinJanniteOK():
	(alhainenJannite1, alhainenJannite2, pudonnutJannite)=regulaattorinJanniteTestit()
	jannitePudonnutKertaa=0
	while pudonnutJannite:
		debug("Regulaattorin jannite on pudonnut. Mitataan uudelleen.")
		(alhainenJannite1, alhainenJannite2, pudonnutJannite)=regulaattorinJanniteTestit()
		jannitePudonnutKertaa+=1;
		if jannitePudonnutKertaa>5:
			debug("Jannite romahtaa.")
	LowVoltage=False;
	if alhainenJannite1 or alhainenJannite2:
		debug("Regulaattorin jannite on kriittisen alhainen")
		LowVoltage=True;

def mittaaKaikkiKanavat():
	value1=mcp.read_adc(IOkanava1);
	value2=mcp.read_adc(IOkanava2);
	value3=mcp.read_adc(IOkanava3);
	value4=mcp.read_adc(IOkanava4);
	value5=mcp.read_adc(IOkanava5);
	return (value1, value2, value3, value4, value5);

# mitataan kutakin kanavaa sekunnin ajan kalibrointi
def mittaaSykli():
	global kanavan1Keskiarvo; global kanavan2Keskiarvo; global kanavan3Keskiarvo;
	mittausLista1temp = [];
	mittausLista2temp = [];
	mittausLista3temp = [];
	for i in range(0, mittauksiaSekunnissa):
		teho1=lueKavavanArvo(IOkanava1);
		mittausLista1temp.append(poistaPoikkeamaAbs(teho1,kanavan1Keskiarvo));
	for j in range(0, mittauksiaSekunnissa):
		teho2=lueKavavanArvo(IOkanava2);
		mittausLista2temp.append(poistaPoikkeamaAbs(teho2,kanavan2Keskiarvo));
	for k in range(0, mittauksiaSekunnissa):
		teho2=lueKavavanArvo(IOkanava3);
		mittausLista3temp.append(poistaPoikkeamaAbs(teho3,kanavan3Keskiarvo));
	return (mittausLista1temp, mittausLista2temp, mittausLista3temp);

# mitataan kutakin kanavaa sekunnin ajan - virtamittaus
def mittaaPowSykli(): # tuottaa 3 sekunnissa neliolliset mittauslistat
	global kanavan1Keskiarvo; global kanavan2Keskiarvo; global kanavan3Keskiarvo;
	mittausLista1temp = [];
	mittausLista2temp = [];
	mittausLista3temp = [];
	for i in range(0, mittauksiaSekunnissa):
		teho1=lueKavavanArvo(IOkanava1);
		teho1=poistaPoikkeama(teho1,kanavan1Keskiarvo); # poikkeama nollasta + tai - # korotetaan toiseen potenssiin
		teho1=math.pow(teho1, 2); # pot 2
		mittausLista1temp.append(teho1);
	for j in range(0, mittauksiaSekunnissa):
		teho2=lueKavavanArvo(IOkanava2);
		teho2=poistaPoikkeama(teho2,kanavan2Keskiarvo);
		teho2=math.pow(teho2, 2);
		mittausLista2temp.append(teho2);	
	for k in range(0, mittauksiaSekunnissa):
		teho3=lueKavavanArvo(IOkanava3);
		teho3=poistaPoikkeama(teho3,kanavan3Keskiarvo);
		teho3=math.pow(teho3, 2);
		mittausLista3temp.append(teho3);
	return (mittausLista1temp, mittausLista2temp, mittausLista3temp);

def mittaaRaakaJanniteSykli(kestoSekunteina=20): # jannitekalibrointiin 20s
	mittausLista1temp = [];
	for i in range(0, kestoSekunteina*mittauksiaSekunnissa):
		jannite=mittaaJanniteRaaka();
		mittausLista1temp.append(jannite);
	# Lasketaan jannitteen keskiarvo
	keskiarvo=10*averageListFloat(mittausLista1temp);
	jannite=laskeJannite(keskiarvo/10);
	debug("Jannitteen raakamittauksen keskiarvo (x 10) : {0} - laskettu jannite on {1}".format(keskiarvo, jannite));
	return (keskiarvo, jannite);

def muunnaVirraksi(mittaus):
	mitattuVirta=mittaus*virtaSkaalausKerroin;
	return mitattuVirta;

def mittausLooppi(): # mittaa 3 sekunnin tehokeskiarvot
	mittausAlkoiMillisec = int(round(time.time() * 1000)) # timestamp in millisec

	global liukuvaTeho1;
	global liukuvaTeho2;
	global liukuvaTeho3;
	# Mitataan jannite
	jannite = mittaaJannite();
	# Mitataan virrat 3 x 1s
	
	if kalibroidaanJannite: 
		average1virta=1; # ensimmainen vaihe palauttaa jannitemittauksen raaka-arvon kymmenkertaisena
		average2virta=(laskeJannite(jannite/10))/jannite*10; # toinen vaihe palauttaa jannitteen nykyisen laskennallisen arvon *10
		average3virta=0.1*average2virta; # kolmas vaihe palauttaa jannitemittauksen pyoristettyna
		mittausKestiMillisec = 1;
		debug("Kalibroidaan jannitemittausta. Saatiin jannitteen raaka-arvo: {0}".format(jannite))
		
	else:
		mittausLista1, mittausLista2, mittausLista3=mittaaPowSykli(); # tuottaa 3 sekunnissa neliolliset mittauslistat
		#lasketaan virrat ja tehot
		average1=averagePowList(mittausLista1);
		average2=averagePowList(mittausLista2);
		average3=averagePowList(mittausLista3);
		average1virta=muunnaVirraksi(average1);
		average2virta=muunnaVirraksi(average2);
		average3virta=muunnaVirraksi(average3);

	average1teho=(average1virta*jannite);
	average2teho=(average2virta*jannite);
	average3teho=(average3virta*jannite);
	
	if varmennetaanKalibrointi: # varmennetaan kalibrointituloksia # Lahetetaan palvelimelle CH1: 10*laskettuvirta1, CH2: 10*laskettujannite, CH3: laskettu teho
		debug("Palautetaan palvelimelle: CH1: 1000*laskettuvirta1, CH2: 10*laskettujannite, CH3: laskettu teho");
		pass;
		average3teho=average1teho;  # CH3: laskettu teho - teho kanava 1 
		average2teho=(jannite*10); # CH2: 10*laskettujannite - kanava 1 - # toinen vaihe palauttaa jannitteen nykyisen laskennallisen arvon *10
		average1teho=1000*average1virta; # CH1: 1000*laskettuvirta1 - kanava 1
		debug("Nyt laskettuvirta1: {0} ; laskettujannite1: {1} ; laskettu teho1 {2}".format(average1teho, average2teho, average3teho));
	pass;
	
	if naytaVirtaMittaus:
		debug ("Keskiarvo-virta(1): " + str(average1virta) + "  -- 30 s jakso");
		debug ("Keskiarvo-virta(2): " + str(average2virta) + "  -- 30 s jakso");
		debug ("Keskiarvo-virta(3): " + str(average3virta) + "  -- 30 s jakso");

	#debug ("Keskiarvo-teho(1): 30s " + str(int(round(average1teho))));
	#palautetaan 3 x 1s tehot
	mittausLoppuiMillisec = int(round(time.time() * 1000)) # timestamp in millisec
	mittausKestiMillisec = mittausLoppuiMillisec - mittausAlkoiMillisec;
	return (average1teho, average2teho, average3teho, mittausKestiMillisec);

##################################################################################################
##################################################################################################
# Apufunktioita laitteen testaamiseen
# esim. mittausten kalibrointia varten

# mitataan kutakin kanavaa sekunnin ajan kalibrointi
def raakaMittaaSykli(mittauksia=183): # mitataan virtamittaukset - palautetaan raakamittaukset listoina
	mittausLista1temp = [];
	mittausLista2temp = [];
	mittausLista3temp = [];
	for i in range(0, mittauksia):
		teho1=lueKavavanArvo(IOkanava1);
		mittausLista1temp.append(teho1);
	for j in range(0, mittauksia):
		teho2=lueKavavanArvo(IOkanava2);
		mittausLista2temp.append(teho2);
	for k in range(0, mittauksia):
		teho3=lueKavavanArvo(IOkanava3);
		mittausLista3temp.append(teho3);
	return (mittausLista1temp, mittausLista2temp, mittausLista3temp); # palauttaa listat

def raakaMittausLooppi(mittaustenLukumaara=183): # mittaa 3 x 1 sekunnin keskiarvot virtamittauksille
	mittausAlkoiMillisec = int(round(time.time() * 1000)) # timestamp in millisec
	# Mitataan kaikki lukuarvot sekunnin ajan
	mittausLista1, mittausLista2, mittausLista3=raakaMittaaSykli(mittaustenLukumaara); # tuottaa 3 sekunnissa mittauslistat
	#keskiarvot
	average1=averageListFloat(mittausLista1);
	average2=averageListFloat(mittausLista2);
	average3=averageListFloat(mittausLista3);
	
	#palautetaan 3 x 1s keskiarvot
	mittausLoppuiMillisec = int(round(time.time() * 1000)) # timestamp in millisec
	mittausKestiMillisec = mittausLoppuiMillisec - mittausAlkoiMillisec;
	return (average1, average2, average3, mittausKestiMillisec); # palauttaa keskiarvot
	
def jannitemittausKalibrointi(mittauksiaKeskiarvoon=183):
	mittausListaJannite = [];
	for i in range(0, mittauksiaKeskiarvoon):
		jannite=mittaaJanniteRaaka()
		mittausListaJannite.append(jannite);
	keskiarvo=averageListFloat(mittausListaJannite);
	debug("Jannitteen raakamittausten keskiarvo: {0}".format(keskiarvo));
	return keskiarvo;

def jannitemittausKalibrointiTiedostoon(keskiarvojaKirjataan=5, mittauksiaKeskiarvoon=1830):
	# tiedostoon janniteraakamittaukset.csv tallennetaan mittausten tiedot: mittaussyklin nro; mittausten lukumaara; mittausten keskiarvo
	keskiarvoListaJannite = [];
	payloadCSV=""
	for i in range(0, keskiarvojaKirjataan):
		keskiarvo=jannitemittausKalibrointi(mittauksiaKeskiarvoon);
		keskiarvoListaJannite.append(keskiarvo);
		mittausTietoString="{0};{1};{2};\n".format(i, mittauksiaKeskiarvoon, keskiarvo)
		payloadCSVold=payloadCSV;  
		payloadCSV=payloadCSVold+mittausTietoString; 
	keskiarvojenKeskiarvo=averageListFloat(keskiarvoListaJannite);
	mittausTietoString="{0};{1};{2};\n".format("ka", keskiarvojaKirjataan*mittauksiaKeskiarvoon, keskiarvojenKeskiarvo)
	payloadCSVold=payloadCSV;  
	payloadCSV=payloadCSVold+mittausTietoString; 
	debug("Jannitteen raakamittausten keskiarvojen keskiarvo: {0}".format(keskiarvojenKeskiarvo));
	writeData("jannitteenraakamittaukset.csv",payloadCSV);	
	return;

def nollavirranKalibrointimittaus(keskiarvojaKirjataan=5,mittauksiaKalibroinnissa=183):
	# tiedostoon nollavirranraakamittaukset.csv tallennetaan mittausten tiedot: mittaussyklin nro; mittausten lukumaara; vaiheen1 virta-mittausten keskiarvo, vaiheen2 virta-mittausten keskiarvo, vaiheen3 virta-mittausten keskiarvo, mittausjakson kesto
	
	keskiarvoListaVirta1 = [];	
	keskiarvoListaVirta2 = [];	
	keskiarvoListaVirta3 = [];	
	aikaleimaLista =[];
	payloadCSV=""
	
	for j in range(0, keskiarvojaKirjataan):
		(keskiArvoraakamittaus1, keskiArvoraakamittaus2, keskiArvoraakamittaus3,liukuvaMittauksetKestiMillisec)=raakaMittausLooppi(mittauksiaKalibroinnissa)
		aikaleimams = int(round(time.time() * 1000)) # timestamp in millisec
		aikaleimaLista.append(aikaleimams);
		keskiarvoListaVirta1.append(keskiArvoraakamittaus1);
		keskiarvoListaVirta2.append(keskiArvoraakamittaus2);
		keskiarvoListaVirta3.append(keskiArvoraakamittaus3);
				
		# Kirjattava data
		mittausTietoString="{0};{1};{2};{3};{4};{5};{6};\n".format(j, aikaleimams, mittauksiaKalibroinnissa,keskiArvoraakamittaus1, keskiArvoraakamittaus2, keskiArvoraakamittaus3, liukuvaMittauksetKestiMillisec);
		debug("Virran raakamittausten keskiarvoja: "+str(mittausTietoString));
		payloadCSVold=payloadCSV;  
		payloadCSV=payloadCSVold+mittausTietoString; 
		
	# Jakso on  mitattu. Kirjataan arvot.
	keskiarvojenKeskiArvoraakamittaus1=averageListFloat(keskiarvoListaVirta1);
	keskiarvojenKeskiArvoraakamittaus2=averageListFloat(keskiarvoListaVirta2);
	keskiarvojenKeskiArvoraakamittaus3=averageListFloat(keskiarvoListaVirta3);
	
	mittausTietoString="{0};{1};{2};{3};{4};{5};{6};\n".format("ka", aikaleimams, keskiarvojaKirjataan*mittauksiaKalibroinnissa,keskiarvojenKeskiArvoraakamittaus1, keskiarvojenKeskiArvoraakamittaus2, keskiarvojenKeskiArvoraakamittaus3, 0);
	payloadCSVold=payloadCSV;  
	payloadCSV=payloadCSVold+mittausTietoString; 
	debug("Virran raakamittausten keskiarvojen keskiarvot: {0}; {1}; {2}".format(keskiarvojenKeskiArvoraakamittaus1, keskiarvojenKeskiArvoraakamittaus2, keskiarvojenKeskiArvoraakamittaus3));

	writeData("nollavirranraakamittaukset.csv", payloadCSV);	
		
	if automaattinenNollaVirranKalibrointi:
		debug("Otetaan uudetNollavirranArvotKayttoon");
		global kanavan1Keskiarvo; global kanavan2Keskiarvo; global kanavan3Keskiarvo;
		kanavan1Keskiarvo=keskiarvojenKeskiArvoraakamittaus1;
		kanavan2Keskiarvo=keskiarvojenKeskiArvoraakamittaus2;
		kanavan3Keskiarvo=keskiarvojenKeskiArvoraakamittaus3;
	
	################ Tallennetaan uudet kalibrointiasetukset nollavirralle ################
	payloadJSON = {}  
	payloadJSON['kalibrointi'] = {'kanavan1Keskiarvo': keskiarvojenKeskiArvoraakamittaus1,
	'kanavan2Keskiarvo': keskiarvojenKeskiArvoraakamittaus2,
	'kanavan3Keskiarvo': keskiarvojenKeskiArvoraakamittaus3,
	'virtaSkaalausKerroin': virtaSkaalausKerroin,
	'janniteSkaalausKerroin': janniteSkaalausKerroin, 
	'janniteNollataso': janniteNollataso,
	'automaattinenNollaVirranKalibrointi': automaattinenNollaVirranKalibrointi
	}
		
	debug(payloadJSON)
	# writeData("uudetKalibrointiasetukset_2.json", str(payloadJSON)); # tama ei toimi, silla ' eika "

	with open('uudetKalibrointiasetukset.json', 'w') as outfile:  
		json.dump(payloadJSON, outfile)
	
	TallentaanVanhojenPaalle=False;
	if TallentaanVanhojenPaalle: # Haluttaessa voitaisiin kirjoittaa uudet kalibrointiarvot vanhojen paalle.
		with open('kalibrointi.json', 'w') as outfile: # tallennetaan kayttoon jatkossakin
			json.dump(payloadJSON, outfile)
	################ Tallennetaan uudet kalibrointiasetukset nollavirralle ################	
	
	return;

##################################################################################################
##################################################################################################

# Testataan jannitemittaus
testataanJannitemittaus=False;

if testataanJannitemittaus:
	mittauksia=60;
	for i in range(0, mittauksia):
		raakaMittausarvo=mittaaJanniteLooppi();
		laskeJannite(raakaMittausarvo);

