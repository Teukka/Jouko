#!/usr/bin/env python
# -*- coding: utf-8 -*-

# BTcom.py - communication via Bluetooth radio (not tested)
# - The program for BT communication was not tested because no Laird RM186 chip with firmware for peripheral device was obtained.
# - UART communication with BT radio via the GPIO is defined in this program component. This component is only used if the device is a control device with the role of BT master or, if the device is switching device that is working as a BT slave.
# BTcom.py - kommunikaatio Bluetooth-radion kautta (BT-kommunikaation toimivuutta ei ole varmistettu, koska peripheral-firmwarella varustettuja Laird RM186 -siruja ei saatu hankittua)
# - GPIO:n kautta tapahtuva UART-kommunikaatio BT-radion kanssa maaritellaan tassa ohjelmakomponentissa. Tata komponenttia kaytetaan vain, mikali laite on ohjauslaite, jonka alaisuudessa toimii BT-kytkinlaite tai, mikali kyseinen laite itse on BT-kytkinlaite.

# import time;
import json;
import time;
import serial;

with open('asetukset.json') as json_general_settings_file:
	asetus	= json.load(json_general_settings_file)
with open('kommunikaatio.json') as json_com_settings_file:
	kommunikaatioasetus	= json.load(json_com_settings_file)
with open('testiasetukset.json') as json_testi_settings_file:
	testiasetus	= json.load(json_testi_settings_file)

debugON=testiasetus['test']['debugON'];# True; # kun 1, niin ei nayteta debug-funktion viesteja

# BT-kytkinlaitteiden osoitteet:
BTlaite_lkm=kommunikaatioasetus['BT']['BTlaite_lkm'];
BTlaiteOsoite1=kommunikaatioasetus['BT']['BTlaite_osoite1'];
BTlaiteOsoite2=kommunikaatioasetus['BT']['BTlaite_osoite2'];
BTlaiteOsoite3=kommunikaatioasetus['BT']['BTlaite_osoite3'];
BTlaiteOsoite4=kommunikaatioasetus['BT']['BTlaite_osoite4'];
BTlaiteNimi1=kommunikaatioasetus['BT']['BTlaite_nimi1']; # Nyt muuttuja ei kaytossa. Voitaisiin kayttaa laitteen tunnistamiseen skannatessa.

if True:
	#define serial port settings # see import serial: ser.write ser.read ser.readline
	ser = serial.Serial(
		port='/dev/ttyAMA0',
		baudrate = 115200,
		parity=serial.PARITY_NONE,
		stopbits=serial.STOPBITS_ONE,
		bytesize=serial.EIGHTBITS,
		timeout=5
		)

# tyhjia alustuksia
viesti=""
reply=""
msg=""
laskuri=0;
alkutagi="<vientinALKU>"
lopputagi="<vientinLOPPU>"

naytaLaitetiedot=True;

##################################################################################
## Perus funk
def debug(data):
	if debugON:
		print (str(data));

if naytaLaitetiedot:
	debug("Naytetaan BT-laitetiedot");
	tiedot="BTlaitteiden lkm: {0} ; BTlaiteOsoite1: {1} ; BTlaiteNimi1: {2}".format(BTlaite_lkm,BTlaiteOsoite1,BTlaiteNimi1);
	debug(tiedot);

# Aja kaytannossa:
# at
# vspc
# connect 01D6F00A6AAD68

# laite on siltaavana 5s – viesti BT-peripheral laitteelle samassa muodossa, jossa se on tullut palvelimelta
# po. (BLE connected)  
# po. (ReadytoSend)
# (Disconnected) --> voidaan yhdistaa seuraavaan laitteeseen# 
# exit – mikali halutaan poistua ohjelmasta
# RM186test --> <RM186IsInBTmode>

############################### BT UART-komentojen maarittelyt ########################################
# Kaynnistettavan ohjelman nimi ja muita komentoja
BTeol='\r'
#BT-komentoja
lairdReset='atz';
joukoStart='VSPC'
joukoStartSlave='VSPP'
joukoExit='exit'
BTJoin='connect'
BTJoin1='connect {0}'.format(BTlaiteOsoite1);
BTJoin2='connect {0}'.format(BTlaiteOsoite2);
BTJoin3='connect {0}'.format(BTlaiteOsoite3);
BTJoin4='connect {0}'.format(BTlaiteOsoite4);

BTGetDevAddrcmd='bdaddr'; # oma osoite
BTscan='scan';
testDeviceMode='RM186test'; # vastaus rm186test   <RM186IsWaitingInATCommandMode> TAI >rm186test <RM186IsRunningJouko>
clearFlashDrive='at&f 1';

debug("BT-join komento: {0}".format(BTJoin1))

############################### BT UART-komentojen maarittelyt ########################################

############################## Kommunikaation konffaus ########################################
# reset variables - for timing
tinydelay=0.1;	# delay for read parameters or short data
writedelay=0.2;	# delay for commands to write SIM800 or longer data
protdelay=1;		# delay for changing protocol values
BTcomdelay=10;		# oli 6 # delay for waiting BT reply
BTjoindelay=2;
BTjoinextradelay=5;
longdelay=5;		# delay for GPRS network communication - xxx 8 s
verylongdelay=15;	# waiting to connect network
resetdelay=7;		# BT softreset delay

############################### Kommunikaation konffaus funktioita ########################################
# -------------------- BT Funktioita ---------------------------------------------
def ATcommandBT(commandStr, delay):
	ser.write(commandStr+BTeol)
	time.sleep(delay)
	reply = ser.read(ser.inWaiting())
	debug(str(commandStr + " palautti: " + reply))
	return reply;

def printToUart(dataToSend, delay):
	ser.write(dataToSend+BTeol)
	time.sleep(delay)
	reply = ser.read(ser.inWaiting())
	debug("BT-kytkinlaite vastasi: {0}".format(reply))
	return reply;

def UARTread(delay):
	time.sleep(delay)
	reply = ser.read(ser.inWaiting())
	debug("Luettiin UARTista: {0}".format(reply))
	return reply;
	
def getMessageContent(viestidata, alkutagi, lopputagi):
	viestinAlku=""
	viestinKeskiLoppu=""
	viestinKeskiosa=""
	viestinLoppu=""
	alkukohta=viestidata.find(alkutagi)
	loppukohta=viestidata.find(lopputagi)
	if (alkukohta>0 and alkukohta<loppukohta):
		#parsitaan:
		viestinAlku,viestinKeskiLoppu=viestidata.split(alkutagi);
		#debug("Viestin alku: " + viestinAlku); # kaikki turha ennen alkutagia
		viestinKeskiosa,viestinLoppu=viestinKeskiLoppu.split(lopputagi);
		#debug("Viestin loppu: " + viestinLoppu); # kaikki turha lopputagin jalkeen
		debug("getMessageContent palauttaa - viestin sisalto: " + str(viestinKeskiosa));
	return viestinKeskiosa;

def clearSerialBuffer():
	debug("Clearing serial buffer");
	serData=ser.read(512);
	debug(serData);
	serData=ser.read(512);
	debug(serData);
	debug("Buffer cleared");

def UARTsyncLaird():
	debug("Sync UART connection by sending multiple AT or ATI commands\n");
	reply=ATcommandBT('AT', protdelay);
	debug("reply1 is: {0}".format(reply));
	reply=ATcommandBT('AT', writedelay);
	debug("reply2 is: {0}".format(reply));
	reply=ATcommandBT('AT', tinydelay);
	debug("reply3 is: {0}".format(reply));
	return reply

def hardReset(): # TODO tarkista toiminta
	debug("Resetoidaan ensin softa. Tama on varmistus, jos hardReset ei ole kytketty.")
	reply=ATcommandBT(joukoExit, protdelay) 
	reply=ATcommandBT(lairdReset, resetdelay) 
	debug("Resetoidaan BT-radio - Hard Reset")
	GPIOhallinta.BTreset();
	time.sleep(resetdelay);
	reply=UARTsyncLaird();
	return;
	
def softReset(): # Poistutaan Jouko-ohjelmasta (jos oli ajossa) ja kaynnistetaan uudelleen
	vastaus=False;
	reply=ATcommandBT(joukoExit, protdelay) 
	reply=ATcommandBT(lairdReset, resetdelay) 
	serData=ser.read(512);
	reply=UARTsyncLaird();
	if ("00" in reply): # TODO tarkasta oikea vastaus. # OLI OK
		vastaus=True;
	else: 
		hardReset();
	return vastaus;

def testRM186(): # TODO tarkista kutsuva ohjelmasykli
	virhe=True;
	laskuri=0
	while virhe:
		laskuri+=1;
		ehto1=0
		ehto2=0
		debug("Tarkistetaan onko RM186 OK.\n");
		# reply=UARTsyncLaird()
		reply=ATcommandBT(testDeviceMode, protdelay)
		ehto1=reply.find('<RM186IsWaitingInATCommandMode>');
		ehto2=reply.find('<RM186IsInBTmode>');
		ehto3=reply.find('E007');
		if ehto3>0:
			debug("UART-komentoa ei tunnistettu. Laitteeseen ei ehka ole asennettu ohjelmistoa. ")
			time.sleep(2);
			debug("Tarkista laitteen tila tarvittaessa asenna ohjelmisto.")
			time.sleep(1);
		if ehto2<1 and ehto1<1:
			reply=100 # ERROR --> RM186 on jumissa #TODO reboot xxx yrita uudelleen
			hardReset();
			debug("Resetoitiin ja tarkistetaan uudelleen onko RM186 OK.\n");
			replySync=UARTsyncLaird()
			time.sleep(1)
			if "00" in replySync:
				reply=ATcommandBT(testDeviceMode, protdelay)
				ehto1=reply.find('<RM186IsWaitingInATCommandMode>');
				ehto2=reply.find('<RM186IsInBTmode>');		
		if ehto1>0:
			reply=1; # RM186 Is Waiting In AT CommandMode
			virhe=False;
		if ehto2>0:
			reply=2; # RM186 Is Running Jouko in BT-mode
			virhe=False;
		if laskuri>10:
			virhe=False; # pakotetaan poistuminen, ettei jaada looppiin ikuisesti
			reply=100; # vikatila
						
	return reply; # reply 1=AT CommandMode ; reply 2 = Running Jouko;

def tyhjennaRM186flash(): # Huom. Kriittinen toiminto. Poistaa kaikki SB-ohjelmat.
	vastaus=False;
	reply=ATcommandBT(joukoExit, protdelay) 
	toimintaTila=testRM186();
	if toimintaTila==1:
		# tyhjennetaan flash
		reply=ATcommandBT(lairdReset, resetdelay) 
		reply=ATcommandBT(clearFlashDrive, 15);
		reply=ATcommandBT(lairdReset, resetdelay) 
	serData=ser.read(512);
	reply=UARTsyncLaird();
	if ("00" in reply): # TODO tarkasta oikea vastaus. # OLI OK
		vastaus=True;
	else: 
		hardReset();
	# asennetaan uudet SB-ohjelmat paaohjelmatasolla
	return vastaus;

	
########################### BT komennot ###########################
def parseBTmessage(viestiParsittavaksi, alkutagi="<vientinALKU>", lopputagi="<vientinLOPPU>"):
	parsittuviesti=""	
	parsittuviesti=getMessageContent(viestiParsittavaksi, alkutagi, lopputagi)
	
	if "(KaikkiOK)" in parsittuviesti:
		debug("kytkinlaitteella ei viela mittadataa.");
		parsittuviesti="";
	return parsittuviesti;

def startJouko(): # start Jouko-BT
	debug("Starting Jouko-software.\n");
	reply=ATcommandBT(joukoStart, protdelay)
	return reply;

def startJoukoSlave(): # start Jouko-BT
	debug("Starting Jouko-software.\n");
	reply=ATcommandBT(joukoStartSlave, protdelay)
	return reply;

def BTcheckReadyToSend(vastaus):
	debug("Checking if connected and ready to Send.\n");
	valmista=False;
	laskuri=0;
	
	if "(ReadytoSend)" in vastaus:
		valmista=True;
	
	while (not valmista) and (laskuri<5):
		vastaus=UARTread(1)
		laskuri+=1;
		if "(ReadytoSend)" in vastaus:
			debug("Viive oli pidempi. Nyt valmista.");
			valmista=True;
	return valmista;
	

def BTJoinCentralToPeripheral(joinKomento=BTJoin1):
	yhteysValmis=False;
	YhteysYrityslaskuri=0
	while (not yhteysValmis) and (YhteysYrityslaskuri<3): # Jaadaan looppiin kunnes yhteys on valmis
		YhteysYrityslaskuri+=1;
		reply=ATcommandBT(joinKomento, BTjoindelay); # TODO: 2s vai lyhyempi.
		yhteysValmis=BTcheckReadyToSend(reply);
	return yhteysValmis;

def BTSend(viesti): # ”(KaikkiOK)”, jos ei mittadataa ja "<RequestForResend>" niin ReSend
	onnistui=False;
	parsittuViesti=""
	alkutagi="<vientinALKU>"
	lopputagi="<vientinLOPPU>"
	viestiKytkinlaitteelle=alkutagi+str(viesti)+lopputagi;
	viive=4; # odotetaan kytkinlaitteen vastausta 4 sekuntia
	vastaus=printToUart(viestiKytkinlaitteelle, viive); # kytkinlaitteen vastaus
	
	if (alkutagi in vastaus) and (lopputagi in vastaus):
		onnistui=True;
		parsittuViesti=parseBTmessage(vastaus, alkutagi, lopputagi);
	else:
		pass;
		return (onnistui,parsittuViesti)
	
	while "<RequestForResend>" in vastaus:
		vastaus=printToUart(viestiKytkinlaitteelle, viive);

	if (alkutagi in vastaus) and (lopputagi in vastaus):
		onnistui=True;
		parsittuViesti=parseBTmessage(vastaus, alkutagi, lopputagi);
	else:
		pass;
		return (onnistui,parsittuViesti)

	return (onnistui,parsittuViesti)


def BTGetDataRate(): # TODO valmis pohja: MUOKATAAN toiseksi
	serData=ser.read(512); # Varmistetaan etta puskuri on tyhja
	debug("putsattiin puskuri ja loytyi")
	debug(serData)
	dataRate=0;
	dataRateStr=""
	serData=ATcommandBT(BTGetDataRateCmd, writedelay);
	# debug ("Vastaus BT get 2 kyselyyn: " + str(serData));
	alkutagi="<VALUE>"
	lopputagi="</VALUE>"
	alkukohta=serData.find(alkutagi)
	loppukohta=serData.find(lopputagi)
	if (alkukohta>0 and alkukohta<loppukohta):
		dataRateStr=getMessageContent(serData, alkutagi, lopputagi); #BT get 2  Haettiin muuttujan arvo GET komennolla: <VALUE>0</VALUE>
		
	# debug("datarate pitaisi olla: " + str(dataRateStr))
	try:
		dataRate=int(dataRateStr);
	except:
		dataRate=0;
	debug("Received dataRate answer: "+str(dataRate));
	
	serData=ser.read(128); # Varmistetaan etta puskuri on tyhja
	debug("putsattiin puskuri ja loytyi")
	debug(serData)
	
	#tarkastetaan data rate eli kaytossa oleva Spreading Factor
	# komennolla: "BT get 2"
	# Jos 0-2: max payload = 59
	# Jos 3: max payload = 123
	# Jos 4-7: max payload = 230
	return dataRate;

def testJoukoBTrunning():
	tilaOK=False;
	toimintaTila=testRM186();
	if toimintaTila==2:
		tilaOK=True;
	if toimintaTila==1:
		# Exit JoukoLora-ohjelmasta
		vastaus=softReset();
		if vastaus: # reset onnistui
			reply=startJouko(); # Kaynnistetaan Jouko-BT
	return tilaOK;
	
################################################### BT CENTRAL - ISOT KOMENNOT ###################################################;
# Python-komennot:

def varmistaBTohjelmisto(): # yritetaan 3 kertaa kaynnistaa BT-ohjelma
	ohjelmaOK=False;
	laskuri=0;
	while (not ohjelmaOK):
		laskuri+=1;
		ohjelmaOK=testJoukoBTrunning()
		if laskuri>3:
			return ohjelmaOK;
	return ohjelmaOK;

def BTCentralInit(): 
	reply=startJouko(); # vspc --> (ReadytoSend)
	return reply;

def BTCentralConnectPeripheral(joinKomento=BTJoin1):
	# Testataan ensin laitteen tila
	yhteysValmis=False;
	BTOhjelmaOK=varmistaBTohjelmisto()
	if BTOhjelmaOK:
		yhteysValmis=BTJoinCentralToPeripheral(joinKomento); 
	return yhteysValmis;
	
def BTCentralSend(viestiKytkinlaitteelle): 
	(onnistui,parsittuViesti)=BTSend(viesti);
	if "(KaikkiOK)" in parsittuviesti: # ei mittadataa
		parsittuviesti="" # palautetaan vain tyhjaviesti, jotta voidaan helposti ketjuttaa kakis viestia
	return (onnistui, parsittuViesti);

# Python-komennot – extra:
def BTCentralExit(): 
	reply=ATcommandBT(joukoExit, protdelay); # exit
	pass;

def BTCentralScan(merkkijono): # scan --> etsi merkkijonoa kytkinlaite1=01D6F00A6AAD68 tai LAIRD RM186_PE
	laiteloydetty=False;
	reply=ATcommandBT(BTscan, 6) 
	if merkkijono in reply:
		laiteloydetty=True;
	return laiteloydetty;

def BTCentralSendToPeripheral(viestiKytkinlaitteelle, lahetaLaitteelleNro=1):
	onnistui=False;
	kytkilaitteenVastaus=""
	joinKomento=BTJoin1
	if lahetaLaitteelleNro==1:
		joinKomento=BTJoin1;
	if lahetaLaitteelleNro==2:
		joinKomento=BTJoin2
	if lahetaLaitteelleNro==3:
		joinKomento=BTJoin3;
	if lahetaLaitteelleNro==4:
		joinKomento=BTJoin4;
	kytkilaitteenVastaus=""
	valmista=BTCentralConnectPeripheral(joinKomento); # connect 01D6F00A6AAD68
	if valmista:
		(onnistui,kytkilaitteenVastaus)=BTCentralSend(viesti);
	return (kytkilaitteenVastaus);
	
def BTHaeOmaLaiteOsoite():
	reply=ATcommandBT(BTGetDevAddrcmd, protdelay);
	return reply;

################################################### BT PERIPHERAL SLAVE - ISOT KOMENNOT ###################################################;
# BTslave-komennot:
def BTSlaveInit(): # kaynnistetaan softa ja alustetaan mainostaminen
	reply=startJoukoSlave(); # vspp --> 
	return reply;
	
def testJoukoBTSlaveRunning():
	debug("Tata ei voida testata. Laite vain mainostaa itseaan, ja yhteys on voimassa vain, kun ohjauslaitteella on asiaa.")
	pass;

# BTSlaveWaitingLoop()
def BTReceive(viesti): # ”(KaikkiOK)”, jos ei mittadataa ja "<RequestForResend>" niin ReSend
	onnistui=False;
	parsittuViesti=""
	vastaus=""
	vastaus2=vastaus
	alkutagi="<vientinALKU>"
	lopputagi="<vientinLOPPU>"
	viestiOhjausLaitteelle=alkutagi+str(viesti)+lopputagi;

	viive=1.5; # odotetaan kytkinlaitteen vastausta 4 sekuntia
	
	vastaus=UARTread(viive); #viestiohjauslaitteelta

	# JOS READ from UART, niin print to UART 
		
	if (alkutagi in vastaus) and (lopputagi in vastaus): # Toivottu tilanne ohjauslaitteen viestin lukeminen: onnistui ensimmaisella viestin lukemisella.
		onnistui=True;
		parsittuViesti=parseBTmessage(vastaus, alkutagi, lopputagi);
		# Lahetetaan mittausdata ohjauslaitteelle
		vastaus2=printToUart(viestiOhjausLaitteelle, viive); # vastaus2 on tarpeeton, jos ensimmainen vastaus sisalsi jo tagit
	else:
		if (alkutagi in vastaus) or (lopputagi in vastaus): # Viestin luettiin osittain. Pyydetaan uudelleen lahetysta.
			pyydaUusintaLahetys="<RequestForResend>"
			vastaus=printToUart(pyydaUusintaLahetys,viive);
			return (onnistui,parsittuViesti)
		
	while "<RequestForResend>" in vastaus or "<RequestForResend>" in vastaus2:
		vastaus2=printToUart(viestiOhjausLaitteelle, viive); # vastaus2 on taas tarpeeton. Se on vain ohjauslaitteen kuittaus saatuun mittausviestiin.

	if (not onnistui) and (alkutagi in vastaus) and (lopputagi in vastaus):
		onnistui=True;
		parsittuViesti=parseBTmessage(vastaus, alkutagi, lopputagi);
		# Lahetetaan mittausdata ohjauslaitteelle
		vastaus2=printToUart(viestiOhjausLaitteelle, viive); # vastaus2 on tarpeeton, jos ensimmainen vastaus sisalsi jo tagit
	else:
		pass;
		# return (onnistui,parsittuViesti)

	return (onnistui,parsittuViesti)

def ReceiveMessageAndReply(viesti): # esimerkki BT-Orjalaitteen-kommunikaatiosta
	# read from file tehdaan BTslaveCOMloopissa
	(onnistui,parsittuViesti)=BTReceive(viesti)
	return (onnistui,parsittuViesti)
	# save to file tehdaan BTslaveCOMloopissa
	
