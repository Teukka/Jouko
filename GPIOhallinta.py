#!/usr/bin/env python
# -*- coding: utf-8 -*-

# GPIOhallinta.py - GPIO definitions and IO commands
# - IO channel definitions and commands for reading and controlling IO. Reading and guiding GPIO is mainly defined in this program component. Only using SPI and UART via GPIO are their separate components (see mittausMCP3008.py (’measure’) and Communication)
# GPIOhallinta.py - GPIO-maarittelyt ja IO-komennot. 
# - IO-kanavien maarittelyt ja komennot IO:n lukemiseksi ja ohjaamiseksi. GPIO:n lukeminen ja ohjaaminen maaritellaan paaosin tassa ohjelmakomponentissa. Vain GPIO:n kautta tapahtuvat SPI-vaylan lukeminen ja UART-kommunikaatio, ovat omina komponentteinaan (ks. mittausMCP3008.py ja kommunikaatio).

import json;
import time;

def debug(data):
	if debugON:
		print (str(data));

# HUOM! oletuksen BCM-numerointi, koska Adafruit_GPIO (--> pakotetaan BOARD)

# Adafruit on "code wrapper" alkuperaiselle RPi.GPIO kirjastolle. Adafruit selkeyttaa komentoja ja IO:n kayttoa.
## Huom! Kaytetaan kirjastoja rinnakkain:
## Adafruit as GPIO ja as SPI
## Rasp.orig as RPi.GPIO 
import Adafruit_MCP3008; # Tuodaan kirjasto MCP3008:n lukemiseen library.
import Adafruit_GPIO.SPI as SPI;
import Adafruit_GPIO as GPIO;
import RPi.GPIO; # Alkuperainen IO-kirjasto. # HUOM! EI import RPi.GPIO as GPIO

with open('testiasetukset.json') as json_testi_settings_file:
	testiasetus	= json.load(json_testi_settings_file)

debugON=testiasetus['test']['debugON'];# True; # kun 1, niin ei nayteta debug-funktion viesteja

# Kommunnikaatiolaitetiedot saattavat ovat tarpeen alusta-IO-funktiossa
with open('kommunikaatio.json') as json_com_settings_file:
	kommunikaatioasetus	= json.load(json_com_settings_file)
GPRSMode = kommunikaatioasetus['com']['GPRSMode']; # True; # 1, jos GPRS-COMM-laite
LoraMode = kommunikaatioasetus['com']['LoraMode']; # False; # 1, jos Lora-laite
BTmode = kommunikaatioasetus['com']['BTmode'];   # True, jos BT-laite GPRS:n alaisuudessa
BTslaveMode = kommunikaatioasetus['com']['BTslaveMode'];   # True, jos tama on BT-orjalaite. Huom! oma looppi

# -------------------------- IO-pinnien numeroinnin maarittely -------------------------------- #
boardNumbering=False; # kun False, niin BNC-numerointi (eli GPIO27 jne.), kun True, niin fyysisten pinnien mukainen numerointi

if (not boardNumbering):
	# OUTPUT:
	RELE_OHJAUS1_OFF = 6;  # (def. LOW) Releohjaus1 - # BOARD 31 – L1_CTRL_OFF (GPIO 6) – vaiherele1
	RELE_OHJAUS2_OFF = 19; # (def. LOW) Releohjaus2 - # BOARD 35 – L2_CTRL_OFF (GPIO 19) – vaiherele2
	RELE_OHJAUS3_OFF = 20; # (def. LOW) Releohjaus3 - # BOARD 38 – L3_CTRL_OFF (GPIO 20) – vaiherele3
		
	RASP_PWR_CTRL = 24; # (def. HIGH) # BOARD 18 – RASP_PWR_CTRL (GPIO 24)

	PWRKEY = 27; # (def. LOW) GPRS pwrkey-output, # BOARD 13 – GSM_PWR (GPIO 27)
	GSM_RESET = 22; # (def. LOW) # BOARD 15 – GSM_RESET (GPIO 22)
	LAIRD_RST = 23; # (def. LOW) # BOARD 16 – LAIRD_RST – inv.  (GPIO 23)
	RASP_LED3_CONTROL = 21; # (def. HIGH) # BOARD 40 – RASP_LED3_CONTROL (GPIO 21)
	
	# UART
	SIMCOM_TALK = 26; # (def. alternate) # BOARD 37 – SIMCOM_TALK (GPIO 26)
	LAIRD_TALK = 5; # (def. alternate) # BOARD 29 – LAIRD_TALK (GPIO 5)
	UART_CTS = 16; # (BOARD 36) - Clear to Send - Rasp haluaa lahettaa - Active LOW - RM186
	UART_RTS = 17; # (BOARD 11) - Request to Receive - Rasp voi vastaanottaa - Active LOW - RM186
	
	# DI-pinni:
	LAIRD_INTEGRITY = 25; # BOARD 22 – INTEGRITY (GPIO 25) – Lairdin pulssi

	# MCP3008
	CLK  = 11; # 22 # default 11	(BOARD 23)
	MISO = 9;  # 27 # default 9		(BOARD 21)
	MOSI = 10; # 17 # default 10	(BOARD 19)
	CS   = 8;  # Laite 0 SPICS0  	(BOARD 24)

if boardNumbering:
	# OUTPUT:
	RELE_OHJAUS1_OFF = 31;  # Releohjaus1 - # BOARD 31 – L1_CTRL_OFF (GPIO 6) – vaiherele1
	RELE_OHJAUS2_OFF = 35; # Releohjaus2 - # BOARD 35 – L2_CTRL_OFF (GPIO 19) – vaiherele2
	RELE_OHJAUS3_OFF = 38; # Releohjaus3 - # BOARD 38 – L3_CTRL_OFF (GPIO 20) – vaiherele3
	
	RASP_PWR_CTRL = 18; # BOARD 18 – RASP_PWR_CTRL (GPIO 24)

	PWRKEY = 13; # GPRS pwrkey-output, # BOARD 13 – GSM_PWR (GPIO 27)
	GSM_RESET = 13; # BOARD 15 – GSM_RESET (GPIO 22)
	LAIRD_RST = 16; # BOARD 16 – LAIRD_RST – inv.  (GPIO 23)
	RASP_LED3_CONTROL = 40; # BOARD 40 – RASP_LED3_CONTROL (GPIO 21)
	
	# UART
	SIMCOM_TALK = 37; # BOARD 37 – SIMCOM_TALK (GPIO 26)
	LAIRD_TALK = 29; #BOARD 29 – LAIRD_TALK (GPIO 5)
	UART_CTS = 36; # (BOARD 36) - Clear to Send - Rasp haluaa lahettaa
	UART_RTS = 11; # (BOARD 11) - Request to Receive - Rasp voi vastaanottaa

	# DI-pinni:
	LAIRD_INTEGRITY = 22; # BOARD 22 – INTEGRITY (GPIO 25) – Lairdin pulssi
	
	# MCP3008
	CLK  = 23;  # default 11		(BOARD 23)
	MISO = 21;  # default 9			(BOARD 21)
	MOSI = 19;  # default 10		(BOARD 19)
	CS   = 24;  # Laite 0 SPICS0  	(BOARD 24)		
	
# -------------------------- IO-toimintatilatesti- ja maarittely-funktiot -------------------------------- #
def testaaGPIOmode():
	# global gpio;
	try:
		if boardNumbering: # jos numerointi pinnien mukaan
			gpio = GPIO.get_platform_gpio(mode=RPi.GPIO.BOARD); # Voidaan pakottaa BOARD-mode;
			RPi.GPIO.setmode(GPIO.BOARD) # pinnit aina samalla paikalla fyysisesti

		if not boardNumbering: # kun BCM-numerointi eli kaytetaan nimettyja GPIO-numeroita
			gpio = GPIO.get_platform_gpio();
			#RPi.GPIO.setmode(GPIO.BCM) # ei turvallinen, kun kaytossa on useita eri laiteversioita
	
		# Test GPIO-mode
		debug("testataan moodi")
		GPIOmode = RPi.GPIO.getmode(); # komento, jos RPi.GPIO
		debug("GPIOhallinta says - GPIO-mode on nyt: " + str(GPIOmode)+" . Jos (10)--> BOARD, jos (11)--> BCM" ) # ollaanko jo BCM-modessa vai BOARD		
	except KeyboardInterrupt:
		debug ("Keskeytetty painamalla ctrl+C");
	except:
		debug ("Keskeytetty jollain muulla tavalla 104");	

if True:
	try:
		if boardNumbering: # jos numerointi pinnien mukaan
			gpio = GPIO.get_platform_gpio(mode=RPi.GPIO.BOARD); # Voidaan pakottaa BOARD-mode;
			RPi.GPIO.setmode(GPIO.BOARD) # pinnit aina samalla paikalla fyysisesti

		if not boardNumbering: # kun BCM-numerointi eli kaytetaan nimettyja GPIO-numeroita
			gpio = GPIO.get_platform_gpio();
			#RPi.GPIO.setmode(GPIO.BCM) # ei turvallinen, kun kaytossa on useita eri laiteversioita
		
		# Test GPIO-mode
		debug("testataan moodi")
		GPIOmode = RPi.GPIO.getmode(); # komento, jos RPi.GPIO
		debug("GPIOhallinta: - GPIO-mode on nyt: " + str(GPIOmode)+" . Jos (10)--> BOARD, jos (11)--> BCM" ) # ollaanko jo BCM-modessa vai BOARD	
		
	except KeyboardInterrupt:
		debug ("Keskeytetty painamalla ctrl+C");
	except:
		debug ("Keskeytetty jollain muulla tavalla 134");	

global mcp;	
def maaritteleMcp():
	mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI);
	return mcp
	
mcp=maaritteleMcp()

# -------------------------- Yleiset IO-funktiot -------------------------------- #
## Kaytetaan RPi-alustuskomentoja, mikali mahdollista. 
## Erityisesti RASP_PWR_CTRL pitaa olla aina HIGH. Siksi alustus heti HIGH-tilaan.
def alustaKanavaOutputOn(kanava): # Init Raspi output 3.3 V
	RPi.GPIO.setup(kanava, GPIO.OUT, initial=GPIO.HIGH);
	debug ("Kanava : " + str(kanava)+ " alustettu ja HIGH (3,3 V) - RPi");

def alustaKanavaOutputOff(kanava): # Init Raspi output 0 V
	RPi.GPIO.setup(kanava, GPIO.OUT, initial=GPIO.LOW);
	debug ("Kanava : " + str(kanava)+ " alustettu ja LOW  (0 V) - RPi");

# Vaihtoehtoisesti voitaisiin kayttaa ADA-komentoja, IO:n alustamiseen ja ohjaamiseen. Nyt eivat kaytossa.
def alustaKanavaOutputOnAda(kanava): # Init Raspi output 3.3 V
	gpio.setup(kanava, GPIO.OUT);
	gpio.output(kanava, GPIO.HIGH);
	debug ("Kanava : " + str(kanava)+ " alustettu ja HIGH (3,3 V) _ ADAfruit");

def alustaKanavaOutputOffAda(kanava): # Init Raspi output 0 V
	gpio.setup(kanava, GPIO.OUT);
	gpio.output(kanava, GPIO.LOW);
	debug ("Kanava : " + str(kanava)+ " alustettu ja LOW  (0 V) _ ADAfruit");

def alustaKanavaInput(kanava): # Init Raspi Input
	gpio.setup(kanava, GPIO.IN);
	# RPi.GPIO.setup(kanava, GPIO.OUT, initial=GPIO.LOW);
	debug ("Kanava : " + str(kanava)+ " alustettu INPUT.");

def kanavaOn(kanava): # Raspi output 3.3 V
	# global gpio
	gpio.output(kanava, GPIO.HIGH);
	debug ("kanava : " + str(kanava)+ " paalle.");
	
def kanavaOff(kanava): # Raspi output 0 V
	# global gpio
	gpio.output(kanava, GPIO.LOW);
	debug ("kanava : " + str(kanava)+ " pois paalta.");

def lueKanava(kanava):
	result=gpio.input(kanava);
	kanavaTieto=False;
	if result==GPIO.HIGH:
		kanavaTieto=True;
	if result==GPIO.LOW:
		kanavaTieto=False;
	return kanavaTieto;

def lueDIkanava(kanava):
	result=gpio.input(kanava);
	return result;

def alustaIO(): # asetetaan kanavat alkuarvoihin
	#global gpio
	try:
		# OUTPUT
		# TODO: Alustetaanko HIGH vai jatetaanko alustamatta?
		alustaKanavaOutputOn(RASP_PWR_CTRL); ## BOARD 18 – RASP_PWR_CTRL (GPIO 24)
		
		debug("Releet johtaviksi.");
		alustaKanavaOutputOff(RELE_OHJAUS1_OFF); # BOARD 31 – L1_CTRL_OFF (GPIO 6) – vaiherele1
		alustaKanavaOutputOff(RELE_OHJAUS2_OFF); # BOARD 35 – L2_CTRL_OFF (GPIO 19) – vaiherele2
		alustaKanavaOutputOff(RELE_OHJAUS3_OFF); # BOARD 38 – L3_CTRL_OFF (GPIO 20) – vaiherele3
		
		debug("Radiot lepaavat.");
		alustaKanavaOutputOff(PWRKEY); ## 13 – GSM_PWR (GPIO 27) # GPRS-radio paalle signaali 1s ja pois 2s
		alustaKanavaOutputOff(GSM_RESET); ## BOARD 15 – GSM_RESET (GPIO 22)
		alustaKanavaOutputOff(LAIRD_RST); ## BOARD 16 – LAIRD_RST – inv.  (GPIO 23) # TODO - tutki on vai off - Oli aluksi OFF
		
		#LED
		alustaKanavaOutputOn(RASP_LED3_CONTROL); ## BOARD 40 – RASP_LED3_CONTROL (GPIO 21)

		if LoraMode or BTslaveMode: # Kun laitteessa LORA-radio tai BT-orjalaite
			debug("UART to Lora - alustus.");
			alustaKanavaOutputOff(SIMCOM_TALK); ## BOARD 37 – SIMCOM_TALK (GPIO 26)
			alustaKanavaOutputOn(LAIRD_TALK); ##BOARD 29 – LAIRD_TALK (GPIO 5)
				
		if GPRSMode: # Kun laitteessa GSM-radio
			debug("UART to SIMCOM.");
			alustaKanavaOutputOn(SIMCOM_TALK); ## BOARD 37 – SIMCOM_TALK (GPIO 26)
			alustaKanavaOutputOff(LAIRD_TALK); ##BOARD 29 – LAIRD_TALK (GPIO 5)
		
		FlowControl=False;
		if FlowControl:
			debug("Alustetaan CTS ja RTS asentoon 0 - active LOW RM186")
			alustaKanavaOutputOff(UART_CTS); # Active LOW
			alustaKanavaOutputOff(UART_RTS); # Active LOW
			
		# INPUT
		alustaKanavaInput(LAIRD_INTEGRITY); ## 22 – INTEGRITY (GPIO 25) – Lairdin pulssi

		debug("GPIO alustettu - GPIOhallinta - alustaIO");

	except KeyboardInterrupt:
		debug ("Keskeytetty painamalla ctrl+C");
	except:
		debug ("Keskeytetty jollain muulla tavalla 237");

def alustaIOAda(): # asetetaan kanavat alkuarvoihin
	#global gpio
	try:
		# OUTPUT
		# TODO: Alustetaanko HIGH vai jatetaanko alustamatta?
		alustaKanavaOutputOnAda(RASP_PWR_CTRL); ## BOARD 18 – RASP_PWR_CTRL (GPIO 24)
		
		debug("Releet johtaviksi.");
		alustaKanavaOutputOffAda(RELE_OHJAUS1_OFF); # BOARD 31 – L1_CTRL_OFF (GPIO 6) – vaiherele1
		alustaKanavaOutputOffAda(RELE_OHJAUS2_OFF); # BOARD 35 – L2_CTRL_OFF (GPIO 19) – vaiherele2
		alustaKanavaOutputOffAda(RELE_OHJAUS3_OFF); # BOARD 38 – L3_CTRL_OFF (GPIO 20) – vaiherele3
		
		debug("Radiot lepaavat.");
		alustaKanavaOutputOffAda(PWRKEY); ## 13 – GSM_PWR (GPIO 27) # GPRS-radio paalle signaali 1s ja pois 2s
		alustaKanavaOutputOffAda(GSM_RESET); ## BOARD 15 – GSM_RESET (GPIO 22)
		alustaKanavaOutputOffAda(LAIRD_RST); ## BOARD 16 – LAIRD_RST – inv.  (GPIO 23) # TODO - tutki on vai off - Oli aluksi OFF
		
		#LED
		alustaKanavaOutputOnAda(RASP_LED3_CONTROL); ## BOARD 40 – RASP_LED3_CONTROL (GPIO 21)

		if LoraMode or BTslaveMode: # Kun laitteessa LORA-radio tai BT-orjalaite
			debug("UART to Lora - alustus.");
			alustaKanavaOutputOffAda(SIMCOM_TALK); ## BOARD 37 – SIMCOM_TALK (GPIO 26)
			alustaKanavaOutputOnAda(LAIRD_TALK); ##BOARD 29 – LAIRD_TALK (GPIO 5)
				
		if GPRSMode: # Kun laitteessa GSM-radio
			debug("UART to SIMCOM.");
			alustaKanavaOutputOnAda(SIMCOM_TALK); ## BOARD 37 – SIMCOM_TALK (GPIO 26)
			alustaKanavaOutputOffAda(LAIRD_TALK); ##BOARD 29 – LAIRD_TALK (GPIO 5)
		
		FlowControl=False;
		if FlowControl:
			debug("Alustetaan CTS ja RTS asentoon 0 - active LOW RM186")
			alustaKanavaOutputOffAda(UART_CTS); # Active LOW
			alustaKanavaOutputOffAda(UART_RTS); # Active LOW
			
		# INPUT
		alustaKanavaInput(LAIRD_INTEGRITY); ## 22 – INTEGRITY (GPIO 25) – Lairdin pulssi

		debug("GPIO alustettu - GPIOhallinta - alustaIO");

	except KeyboardInterrupt:
		debug ("Keskeytetty painamalla ctrl+C");
	except:
		debug ("Keskeytetty jollain muulla tavalla 284");

# -------------------------- UART valinta Laird, SIMCOM tai IRTI -------------------------------- #
def alustaFlowControlUARTon():
	debug("Alustetaan CTS ja RTS asentoon 0 - active LOW RM186")
	alustaKanavaOutputOff(UART_CTS); # Active LOW
	alustaKanavaOutputOff(UART_RTS); # Active LOW

def alustaFlowControlUARToff():
	alustaKanavaOutputOn(UART_CTS); # Active LOW
	alustaKanavaOutputOn(UART_RTS); # Active LOW

def UART_on():
	kanavaOff(UART_CTS); # Active LOW - RM186
	kanavaOff(UART_RTS); # Active LOW - RM186

def UART_off():
	kanavaOn(UART_CTS); # Active LOW - RM186
	kanavaOn(UART_RTS); # Active LOW - RM186
	
## UART voidaan valita siten, etta joko LAIRD, tai SIMCOM vaylaa
def selectUARTmode(valinta): # valinta: 0=UART IRTI, 1=LAIRD_TALK_UART, 2=SIMCOM_TALK_UART
	if valinta==1:
		LAIRD_TALK_UART=True;
		kanavaOff(SIMCOM_TALK);
		kanavaOn(LAIRD_TALK); # LAIRD_TALK = 5; #BOARD 29 – LAIRD_TALK (GPIO 5)
		# UART_on();
	if valinta==2:
		SIMCOM_TALK_UART=True;
		kanavaOff(LAIRD_TALK);
		kanavaOn(SIMCOM_TALK); # SIMCOM_TALK = 26; # BOARD 37 – SIMCOM_TALK (GPIO 26)
		# UART_on();
	else: 
		# muutoin UART on irti
		kanavaOff(LAIRD_TALK);
		kanavaOff(SIMCOM_TALK);
		# UART_off();

def UART_to_LAIRD():
	# selectUARTmode(1)
	debug("UART to Laird Lora.")
	kanavaOff(SIMCOM_TALK);
	kanavaOn(LAIRD_TALK); # LAIRD_TALK = 5; #BOARD 29 – LAIRD_TALK (GPIO 5)
	# UART_on();

def UART_to_SIMCOM():
	# selectUARTmode(2)
	debug("UART to SIMCOM GSM.")
	kanavaOff(LAIRD_TALK);
	kanavaOn(SIMCOM_TALK); # SIMCOM_TALK = 26; # BOARD 37 – SIMCOM_TALK (GPIO 26)
	# UART_on();

def UART_all_up(): # testi, po. irti - turha TODO poista
	# selectUARTmode(1)
	debug("UART IRTI 2 - ALL UP.")
	kanavaOn(SIMCOM_TALK);
	kanavaOn(LAIRD_TALK); 
	# UART_off();
	
def UARTirti():
	# selectUARTmode(0)
	kanavaOff(LAIRD_TALK);
	kanavaOff(SIMCOM_TALK);
	# UART_off();
	
# -------------------------- UART valinta Laird, SIMCOM tai IRTI -------------------------------- #
				
def resetoiIOalkuarvoihin(): # asetetaan kanavat alkuarvoihin
	try:
		kanavaOn(RASP_PWR_CTRL); ## BOARD 18 – RASP_PWR_CTRL (GPIO 24)
		
		debug("Releet johtaviksi.");
		kanavaOff(RELE_OHJAUS1_OFF); # BOARD 31 – L1_CTRL_OFF (GPIO 6) – vaiherele1
		kanavaOff(RELE_OHJAUS2_OFF); # BOARD 35 – L2_CTRL_OFF (GPIO 19) – vaiherele2
		kanavaOff(RELE_OHJAUS3_OFF); # BOARD 38 – L3_CTRL_OFF (GPIO 20) – vaiherele3
		
		debug("Radiot lepaavat.");
		kanavaOff(PWRKEY); ## 13 – GSM_PWR (GPIO 27) # GPRS-radio paalle signaali 1s ja pois 2s
		kanavaOff(GSM_RESET); ## BOARD 15 – GSM_RESET (GPIO 22)
		kanavaOff(LAIRD_RST); ## BOARD 16 – LAIRD_RST – inv.  (GPIO 23)
		#LED
		kanavaOn(RASP_LED3_CONTROL); ## BOARD 40 – RASP_LED3_CONTROL (GPIO 21)
		
		#UART
		kanavaOff(UART_CTS); # active LOW on Laird
		kanavaOff(UART_RTS); # active LOW on Laird

		if LoraMode: # Kun laitteessa LORA-radio
			UART_to_LAIRD();
			debug("UART to Lora.");
			# kanavaOff(SIMCOM_TALK); ## BOARD 37 – SIMCOM_TALK (GPIO 26)
			# kanavaOn(LAIRD_TALK); ##BOARD 29 – LAIRD_TALK (GPIO 5)
				
		if GPRSMode: # Kun laitteessa GSM-radio
			debug("UART to SIMCOM.");
			UART_to_SIMCOM();
			# kanavaOn(SIMCOM_TALK); ## BOARD 37 – SIMCOM_TALK (GPIO 26)
			# kanavaOff(LAIRD_TALK); ##BOARD 29 – LAIRD_TALK (GPIO 5)
		
		debug("GPIO resetoitu alkuarvoihin - GPIOhallinta - resetoiIOalkuarvoihin");

	except KeyboardInterrupt:
		debug ("Keskeytetty painamalla ctrl+C");
	except:
		debug ("Keskeytetty jollain muulla tavalla 194");

def vapautaIO():
	try:
		debug("Poistetaan IO-maarittelyt.")
		RPi.GPIO.cleanup()
		# gpio.rpi_gpio.cleanup()
	except:
		debug("IO vapautus keskeytyi")
		pass
		
def vapautaIOAda():
	try:
		debug("Poistetaan IO-maarittelyt.")
		# RPi.GPIO.cleanup()
		gpio.rpi_gpio.cleanup()
	except:
		debug("IO vapautus keskeytyi")
		pass

# -------------------------- Yleiset funktiot IO -------------------------------- #

# -------------------------- RELE -------------------------------- #
global releenAsento; # releenAsento on kaikille releille sama tassa laiteversiossa
releenAsento=None;

def avaaRele():
	global releenAsento;
	kanavaOn(RELE_OHJAUS1_OFF);
	kanavaOn(RELE_OHJAUS2_OFF);
	kanavaOn(RELE_OHJAUS3_OFF);
	releenAsento=True;

def suljeRele():
	global releenAsento;
	kanavaOff(RELE_OHJAUS1_OFF);
	kanavaOff(RELE_OHJAUS2_OFF);
	kanavaOff(RELE_OHJAUS3_OFF);
	releenAsento=False;

def lueReleenAsento():
	asento=lueKanava(RELE_OHJAUS1_OFF);
	return asento;

#EXTRA - ei tarvita tassa Jouko-versiossa
def lueReleTieto1(): # kaytetaan kuvaamaan koko releen asentoa. true=katko, false=rele kiinni
	asento=lueKanava(RELE_OHJAUS1_OFF);
	return asento;
def lueReleTieto2():
	asento=lueKanava(RELE_OHJAUS2_OFF);
	return asento;
def lueReleTieto3():
	asento=lueKanava(RELE_OHJAUS3_OFF);
	return asento;

def suljeRele1():
	kanavaOff(RELE_OHJAUS1_OFF);
def suljeRele2():
	kanavaOff(RELE_OHJAUS2_OFF);
def suljeRele3():
	kanavaOff(RELE_OHJAUS3_OFF);
def avaaRele1():
	kanavaOn(RELE_OHJAUS1_OFF);
def avaaRele2():
	kanavaOn(RELE_OHJAUS2_OFF);
def avaaRele3():
	kanavaOn(RELE_OHJAUS3_OFF);
# -------------------------- RELE -------------------------------- #

# ------------------------ LED3 Joukon kotelossa -------------------------------- #
def LED3on():
	kanavaOn(RASP_LED3_CONTROL);
def LED3off():
	kanavaOff(RASP_LED3_CONTROL);
# ------------------------ LED3 Joukon kotelossa -------------------------------- #

def LED3vilkutus(vilkutuskertoja=1, vilkutusnopeus=1):
	debug("- LED3vilkutus - LED vilkutus: {0} x {1} s (x2)".format(vilkutuskertoja,vilkutusnopeus));
	for i in range(0, vilkutuskertoja):
		LED3off();
		time.sleep(vilkutusnopeus)
		LED3on();
		time.sleep(vilkutusnopeus)
	
# -------------------------- Raspberry self BOOT  -------------------------------- #
# Raspin power ohjauspinnin kytkeminen pois vahaksi aikaa
def RaspinPowerOhjausOff(): ## Taman pitaisi sammuttaa Raspi
	kanavaOff(RASP_PWR_CTRL);
	time.sleep(0.002);
	kanavaOn(RASP_PWR_CTRL);

def resetSelf():
	debug("Ajetaan RaspberryReset - laitteen uudelleen kaynnistys - katkaisemalla virta.")
	time.sleep(1);
	RaspinPowerOhjausOff();
	time.sleep(3);
	debug("Reset ajettu. Tama viesti ei nay kayttajaAjetaan RaspberryReset - laitteen uudelleen kaynnistys - katkaisemalla virta.")
# -------------------------- Raspberry self BOOT  -------------------------------- #


# -------------------------- SIMCOM GPRS GSM -------------------------------- #
def GPRSpaalle(): # PWRKEY = 27; # GPRS pwrkey-output, # BOARD 13 – GSM_PWR (GPIO 27)
	debug("Ajetaan lyhyt powerKey - paallekytkenta.")
	kanavaOn(PWRKEY)
	time.sleep(1.5) # min 0.9 riittaa kytkemaan paalle
	# TODO muuta aika isommaksi ja tarkistetaan toiminta kutsuvalla tasolla
	kanavaOff(PWRKEY)

def GPRSpois():
	debug("Ajetaan pitka powerKey - poiskytkenta.")
	kanavaOn(PWRKEY)
	time.sleep(2.5) # min 1.02 riittaa kytkemaan pois
	kanavaOff(PWRKEY)

def GPRSreset(): # 15 – GSM_RESET (GPIO 22)
	debug("Ajetaan GSM reset - GPRS radion uudelleen kaynnistys.")
	kanavaOn(GSM_RESET)
	time.sleep(3) # TODO: valitse sopiva reset-aika
	kanavaOff(GSM_RESET)
	
def kytkeSimcomPwrPaalle():
	GPRSpaalle();

def kytkeSimcomPwrPois():
	GPRSpois();
# ------------------------ SIMCOM -------------------------------- #

# -------------------------- LAIRD RM186 LORA -------------------------------- #
def LORAreset(): # LAIRD_RST = 23; # BOARD 16 – LAIRD_RST – inv.  (GPIO 23)
	debug("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
	debug("Resetoidaan Laird RM186.")
	kanavaOn(LAIRD_RST); # REVERSED - Vaihdettu pe klo 17.11 # Toimiva 11.9.2018
	time.sleep(1)
	LED3vilkutus(vilkutuskertoja=1, vilkutusnopeus=0.5); # odotetaan 5 s
	kanavaOff(LAIRD_RST);
	time.sleep(1)
	

def LORAresetInverted(): # LAIRD_RST = 23; # BOARD 16 – LAIRD_RST – inv.  (GPIO 23)
	debug("------------------------------------------------------------------------------------------------------------------")
	debug("Resetointaan Laird RM186 - invertoidut IO-ohjaukset.")
	kanavaOff(LAIRD_RST);
	time.sleep(5)
	LED3vilkutus(vilkutuskertoja=5, vilkutusnopeus=0.5); # odotetaan 5 s
	kanavaOn(LAIRD_RST);
	time.sleep(5)

def lueLORAintegrity():
	IntegrityTila=lueDIkanava(LAIRD_INTEGRITY)
	return IntegrityTila;
# -------------------------- LAIRD RM186 LORA -------------------------------- #


####################################################################################################################
  ############### TESTI FUNKTIOITA ############## TESTI FUNKTIOITA ############## TESTI FUNKTIOITA ##############
####################################################################################################################

# Raspin power ohjauspinnin alustus
def alustaRaspinPowerOhjausOn():
	alustaKanavaOutputOn(RASP_PWR_CTRL); ## BOARD 18 – RASP_PWR_CTRL (GPIO 24)

# ------------ DEMO sekvensseja ---------------------- #
def lueReleidenAsentotiedot():
	global releenAsento;
	rele1=lueReleTieto1(); # true=katko, false=rele kiinni
	rele2=lueReleTieto2();
	rele3=lueReleTieto3();
	debug("RELE_OHJAUS1_OFF tila: 'true'=rele avoin, 'false'=rele kiinni");
	debug("GLOBAL RELE_OHJAUS1_OFF -muuttuja on arvossa: " + str(releenAsento))
	debug("LUE-KANAVA - RELE_OHJAUS1_OFF on arvossa: " + str(rele1))	
	debug("LUE-KANAVA - RELE_OHJAUS2_OFF on arvossa: " + str(rele2))	
	debug("LUE-KANAVA - RELE_OHJAUS3_OFF on arvossa: " + str(rele3))	

def suljeReleetYksitellen():
	debug("Suljetaan kaikki RELEET yksitellen - kanavaOn(rele_kanava)");
	time.sleep(1)
	debug("Suljetaan RELE1");
	suljeRele1();
	time.sleep(1)
	lueReleidenAsentotiedot();
	time.sleep(1)
	debug("Suljetaan RELE2");
	suljeRele2();
	time.sleep(1)
	lueReleidenAsentotiedot();	
	time.sleep(1)
	debug("Suljetaan RELE3");
	suljeRele3();
	time.sleep(1)
	lueReleidenAsentotiedot();	
	time.sleep(1)

def avaaReleetYksitellen():
	debug("Avataan kaikki RELEET yksitellen - kanavaOff(rele_kanava)");
	time.sleep(1)
	debug("Avataan RELE1");
	avaaRele1();
	time.sleep(1)
	lueReleidenAsentotiedot();
	time.sleep(1)
	debug("Avataan RELE2");
	avaaRele2();
	time.sleep(1)
	lueReleidenAsentotiedot();	
	time.sleep(1)
	debug("Avataan RELE3");
	avaaRele3();
	time.sleep(1)
	lueReleidenAsentotiedot();	
	time.sleep(1)
	
def releidenTestiSykli():
	global releenAsento;
	debug("Alustetaan IO");
	alustaIO()
	debug("----------------- ALUSSA kaikki releet suljettu ------------------")
	lueReleidenAsentotiedot();
	time.sleep(1)
	debug("Avataan kaikki RELEET - avaaRele()");
	avaaRele()
	time.sleep(1)
	debug("----------------- RELE AVOINNA ------------------")
	lueReleidenAsentotiedot();	
	time.sleep(1)
	suljeRele()
	debug("----------------- RELE SULJETTU ------------------")
	lueReleidenAsentotiedot();	
	time.sleep(1)
	debug("GLOBAL RELE_OHJAUS1_OFF on arvossa: " + str(releenAsento))
	time.sleep(2)
	
	debug("----------------- Sykli on loppu. Vapautetaan IO.------------------")
	vapautaIO()

def testiSykli():
	global releenAsento;
	alustaIO()
	time.sleep(2)
	debug("----------------- RELE ALUSSA ------------------")
	arvo=lueKanava(RELE_OHJAUS1_OFF)
	debug("LUE-KANAVA - RELE_OHJAUS1_OFF on arvossa: " + str(arvo))	
	debug("RELE_OHJAUS1_OFF on arvossa: " + str(releenAsento))
	time.sleep(2)
	
	suljeRele()
	debug("----------------- RELE SULJETTU ------------------")
	
	arvo=lueReleTieto1()
	debug("LUE-KANAVA - RELE_OHJAUS1_OFF on arvossa: " + str(arvo))	
	debug("RELE_OHJAUS1_OFF on arvossa: " + str(releenAsento))
	time.sleep(1)
	
	avaaRele()
	arvo=lueReleTieto1()
	debug("----------------- RELE AVATTU ------------------")
	debug("LUE-KANAVA - RELE_OHJAUS1_OFF on arvossa: " + str(arvo))	
	debug("RELE_OHJAUS1_OFF on arvossa: " + str(releenAsento))
	
	suljeRele()
	arvo=lueReleTieto1()
	debug("----------------- RELE SULJETTU ------------------")
	debug("LUE-KANAVA - RELE_OHJAUS1_OFF on arvossa: " + str(arvo))	
	debug("RELE_OHJAUS1_OFF on arvossa: " + str(releenAsento))
	time.sleep(1)
	
	debug("----------------- Sykli on loppu. Vapautetaan IO.------------------")
	vapautaIO()
	
def avaaGPRSjaOdota():
	UART_to_SIMCOM();
	debug("UART on auki SIMCOM")
	time.sleep(2)
	debug("GPRS PowerKey short")
	GPRSpaalle()
	time.sleep(60)
	debug("GPRS reset")
	GPRSreset()
	time.sleep(60)
	debug("GPRS PowerKey long")
	GPRSpois()
	time.sleep(60)
	debug("sleep")
	time.sleep(60)
		
def avaaLORAjaOdota():
	UART_to_LAIRD();
	debug("UART on auki Laird Lora")
	time.sleep(2)
	debug("Lora RESET")
	LORAreset()
	time.sleep(60)
	debug("GPRS reset")
	GPRSreset()
	time.sleep(60)
	debug("GPRS PowerKey long")
	GPRSpois()
	time.sleep(60)
	debug("sleep")
	time.sleep(60)
	
## GPRS paalle 2s ja pois 2s
def demoGPRSsykli():
	try:
		alustaIO();
		GPRSpaalle();
		debug("Odotellaan");
		time.sleep(2); # jo 1 s riittaa
		GPRSpois();
		debug("Odotellaan");
		time.sleep(2) # jo 1 s riittaa
	except KeyboardInterrupt:
		debug ("Keskeytetty painamalla ctrl+C");
	except:
		debug ("Keskeytetty jollain ihme tavalla");
	debug ("Testi on ohi.");
	vapautaIO()

def downAndUpGPRSModem():
	try:
		time.sleep(1) # turha
		debug("Ajetaan GPRSpois()")
		GPRSpois()
		debug("Odotellaan")
		time.sleep(2) # jo 1 s riittaa
		debug("Resetoidaan()")
		GPRSreset(); # varmistus
		time.sleep(2) # turha
		debug("Ajetaan GPRSpaalle()")
		GPRSpaalle();
		time.sleep(2) # jo 1 s riittaa
	except KeyboardInterrupt:
		debug ("Keskeytetty painamalla ctrl+C");
	except:
		debug ("Keskeytetty jollain ihme tavalla");
	debug ("Kaytettiin modeemia alhaalla.")

def UARTtestaus():
	alustaIO();
	if GPRSMode:
		avaaGPRSjaOdota(); # kun GPRS
	if LoraMode:
		debug("testi puuttuu - ks. IOtestit")
	vapautaIO();

############# TESTIKOMENTOJA ############# TESTIKOMENTOJA ############# TESTIKOMENTOJA ############# TESTIKOMENTOJA ############# 
# Testaa GPIO ja GPRS PWRkey-demo
# demoGPRSsykli()

## Sykli: Alusta IO - uudelleen kaynnista GPRS ja vapauta IO
# alustaIO()
# downAndUpGPRSModem()
# vapautaIO()

## Testisykli Avaa ja sulkee releet (alustaa ja vapauttaa IO:n)
# testiSykli(); 

## Testisykli Avaa ja sulkee releet lisaksi yksitellen (alustaa ja vapauttaa IO:n)
#releidenTestiSykli();


############# TESTIKOMENTOJA ############# TESTIKOMENTOJA ############# TESTIKOMENTOJA ############# TESTIKOMENTOJA ############# 

####### JEMMA JEMMA ############### JEMMA JEMMA ############### JEMMA JEMMA ############### JEMMA JEMMA ########
####### JEMMA JEMMA ############### JEMMA JEMMA ############### JEMMA JEMMA ############### JEMMA JEMMA ########
# Laitteen IO-maarittelyt:
# esitystapa: fyysinen_laitepinni_numero - IO_nimi (GPIO pinni_numero)
#
# DO-pinnit
# 13 – GSM_PWR (GPIO 27)
# 15 – GSM_RESET (GPIO 22)
# 16 – LAIRD_RST – inv.  (GPIO 23)
# 18 – RASP_PWR_CTRL (GPIO 24)
# 37 – SIMCOM_TALK (GPIO 26)
# 29 – LAIRD_TALK (GPIO 5)
# 31 – L1_CTRL_OFF (GPIO 6) – vaiherele1
# 35 – L2_CTRL_OFF (GPIO 19) – vaiherele2
# 38 – L3_CTRL_OFF (GPIO 20) – vaiherele3

# DI-pinni?
# 22 – INTEGRITY (GPIO 25) – Lairdin pulssi

####### JEMMA JEMMA ############### JEMMA JEMMA ############### JEMMA JEMMA ############### JEMMA JEMMA ########
#testaaGPIOmode(); # testi TODO poista


