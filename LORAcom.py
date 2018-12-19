#!/usr/bin/env python
# -*- coding: utf-8 -*-

# LORAcom.py - communication via LoRa radio
# - GPIO UART communication with the RM186 LoRa radio is defined in this program component. This component is only used if the RM186 LoRa radio is in use.
# LORAcom.py - kommunikaatio LoRa-radion kautta
# - GPIO:n kautta tapahtuva UART-kommunikaatio RM186 LoRa-radion kanssa maaritellaan tassa ohjelmakomponentissa. Tata komponenttia kaytetaan vain, mikali laitteessa on kaytossa RM186 LoRa-radio.

import time;
# import RPi.GPIO as GPIO
import serial;
import GPIOhallinta;

ser = serial.Serial(
	port='/dev/ttyAMA0',
	baudrate = 115200,
	parity=serial.PARITY_NONE,
	stopbits=serial.STOPBITS_ONE,
	bytesize=serial.EIGHTBITS,
	timeout=5 # tutki sopiva arvo - ei voi olla 1 tai get datarate sekoaa - 5 toimii
	)
	
debugON = True; # kun 1, niin ei nayteta debug-funktion viesteja
	
def debug(data):
	if debugON:
		print (str(data));

reply=""
reply2=""
ehto=""
ehto1=""
ehto2=""
testi=False

############################### Lora UART-komentojen maarittelyt ########################################
# Kaynnistettavan ohjelman nimi ja muita komentoja
loraEOL='\r'
#Lora-komentoja
lairdReset='atz'#+loraEOL;
joukoStart="cmd"#+loraEOL;
joukoExit="exit"#+loraEOL;
loraJoin="lora join"#+loraEOL;
loraGetDataRateCmd='lora get 2'#+loraEOL; # >lora get 2  Haettiin muuttujan arvo GET komennolla: <VALUE>0</VALUE>
loraGetJoinStateCmd='lora get 3'#+loraEOL; # >lora get 3  Haettiin muuttujan arvo GET komennolla: <VALUE>Joined</VALUE> tai <VALUE>Not Joined</VALUE> 
loraGetDevEUIcmd='lora get 4'; #+loraEOL; # >lora get 4 
loraGetDevAddrcmd='lora get 6';

testDeviceMode='RM186test'#+loraEOL; # vastaus rm186test   <RM186IsWaitingInATCommandMode> TAI >rm186test <RM186IsRunningJouko>
lastMessage='show'#+loraEOL;

clearFlashDrive='at&f 1'#+loraEOL;

# LoRa Received downstream data on port 1  
# RSSI: -39 SNR: 30 
# <INCOMINGDATA>Viestilaitteelle1</INCOMINGDATA>


############################### Lora UART-komentojen maarittelyt ########################################

############################## Kommunikaation konffaus ########################################
# reset variables - for timing
tinydelay=0.1;	# delay for read parameters or short data
writedelay=0.2;	# delay for commands to write SIM800 or longer data
startdelay=0.5; # delay for starting program
protdelay=1;		# delay for changing protocol values
loracomdelay=10;		# oli 6 # delay for waiting Lora reply
lorajoindelay=10;
lorajoinextradelay=5;
longdelay=5;		# delay for GPRS network communication - xxx 8 s
verylongdelay=15;	# waiting to connect network
resetdelay=7;		# LoRa softreset delay


############################### Kommunikaation konffaus funktioita ########################################
# -------------------- Lora Funktioita ---------------------------------------------
def ATcommandLora(commandStr, delay):
	ser.write(commandStr+loraEOL)
	time.sleep(delay)
	reply = ser.read(ser.inWaiting())
	debug(str(commandStr + " palautti: " + reply))
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
	# debug(serData);
	debug("Buffer cleared");

def sendEmptyAndClear():
	debug("Puhdistetaan UART-vayla ja puskurit yhdella AT-komennolla.\n");
	serData=ser.read(512);
	reply=ATcommandLora('', tinydelay);

def UARTsyncLaird():
	debug("Synkronoidaan  UART lahettamalla AT-komentoja.\n");
	reply=ATcommandLora('AT', writedelay);
	debug("AT reply1 is: {0}".format(reply));
	reply=ATcommandLora('AT', writedelay);
	debug("AT reply2 is: {0}".format(reply));
	reply=ATcommandLora('AT', tinydelay);
	debug("AT reply3 is: {0}".format(reply));
	return reply

def hardReset():
	# debug("Resetoidaan ensin ohjelmisto. Tama on varmistus, jos hardReset ei jostain syysta ole kytketty.")
	# reply=ATcommandLora(joukoExit, protdelay) 
	# reply=ATcommandLora(lairdReset, resetdelay) 
	debug("Resetoidaan Lora-radio - Hard Reset")
	GPIOhallinta.LORAreset();
	time.sleep(resetdelay);
	reply=UARTsyncLaird();
	return;
	
def softReset(): # Poistutaan Jouko-ohjelmasta (jos oli ajossa) ja kaynnistetaan uudelleen
	vastaus=False;
	reply=ATcommandLora(joukoExit, protdelay) 
	reply=ATcommandLora(lairdReset, resetdelay) 
	serData=ser.read(512);
	reply=UARTsyncLaird();
	if ("00" in reply): # TODO tarkasta oikea vastaus. # OLI OK
		vastaus=True;
	else: 
		hardReset();
	return vastaus;

def testRM186(): # TODO tarkista kutsuva ohjelmasykli
	virhe=True;
	sendEmptyAndClear(); # Puhdistetaan UART ja puskurit
	while virhe:
		ehto1=0
		ehto2=0
		debug("Tarkistetaan onko RM186 OK.\n");
		reply=ATcommandLora(testDeviceMode, protdelay)
		ehto1=reply.find('<RM186IsWaitingInATCommandMode>');
		ehto2=reply.find('<RM186IsRunningJouko>');
		ehto3=reply.find('E007');
		if ehto3>0:
			debug("UART-komentoa ei tunnistettu. Laitteeseen ei ehka ole asennettu ohjelmistoa. ")
			time.sleep(5);
			debug("Tarkista laitteen tila tarvittaessa asenna ohjelmisto.")
			time.sleep(1);
		if ehto2<1 and ehto1<1:
			reply=100 # ERROR --> RM186 on jumissa #TODO reboot xxx yrita uudelleen
			hardReset();
			debug("Resetoitiin ja tarkistetaan uudelleen onko RM186 OK.\n");
			replySync=UARTsyncLaird();
			if "00" in replySync:
				reply=ATcommandLora(testDeviceMode, protdelay)
				ehto1=reply.find('<RM186IsWaitingInATCommandMode>');
				ehto2=reply.find('<RM186IsRunningJouko>');
		if ehto1>0:
			reply=1; # RM186 Is Waiting In AT CommandMode
			virhe=False;
		if ehto2>0:
			reply=2; # RM186 Is Running Jouko
			virhe=False;
						
	return reply

def puhdistaRM186flashRaaka():
	reply=ATcommandLora(lairdReset, resetdelay);
	reply=ATcommandLora(clearFlashDrive, 15);
	reply=ATcommandLora(lairdReset, resetdelay);
	return reply;

def tyhjennaRM186flash(): # Huom. Kriittinen toiminto. Poistaa kaikki SB-ohjelmat.
	vastaus=False;
	reply=ATcommandLora(joukoExit, protdelay) 
	
	softResetOnnistuu=softReset(); # Kokeillaan soft-reset.
	if (not softResetOnnistuu): # Jos ei soft, niin hard.
		hardReset(); 
			
	serData=ser.read(512);
	reply=UARTsyncLaird();
	if ("00" in reply): # '00' ilmaisee, etta laite on valmis vastaanottamaan AT-komentoja.
		vastaus=True;
	else: 
		hardReset();
	
	debug("Resetoidaan radio ja tyhjennetaan flash.")
	puhdistaRM186flashRaaka();
	
	serData=ser.read(512);
	reply=UARTsyncLaird();
	if not reply:
		hardReset();
		reply=UARTsyncLaird();
		puhdistaRM186flashRaaka();
		reply=UARTsyncLaird();
		
	if ("00" in reply): # '00' ilmaisee, etta laite on valmis vastaanottamaan AT-komentoja.
		vastaus=True;
		
	# asennetaan uudet SB-ohjelmat kutsuvalla paaohjelmatasolla
	return vastaus;

def startJouko():
	debug("Kaynnistetaan Jouko-ohjelmisto RM186-piirissa.\n");
	reply=ATcommandLora(joukoStart, startdelay)
	return reply

def LoraJoin():
	reply=ATcommandLora(loraJoin, lorajoindelay);
	return reply

def LoraGetDataRate():
	serData=ser.read(512); # Varmistetaan etta puskuri on tyhja
	debug("Tyhjennettiin UART-puskuri ja loytyi: ")
	debug(serData)
	dataRate=0;
	dataRateStr=""
	serData=ATcommandLora(loraGetDataRateCmd, writedelay);
	alkutagi="<VALUE>"
	lopputagi="</VALUE>"
	alkukohta=serData.find(alkutagi)
	loppukohta=serData.find(lopputagi)
	if (alkukohta>0 and alkukohta<loppukohta):
		dataRateStr=getMessageContent(serData, alkutagi, lopputagi); #lora get 2  Haettiin muuttujan arvo GET komennolla: <VALUE>0</VALUE>
		
	try:
		dataRate=int(dataRateStr);
	except:
		dataRate=0;
	debug("Lora dataRate on: "+str(dataRate));
	
	serData=ser.read(128); # Varmistetaan etta puskuri on tyhja
	debug("Tyhjennettiin UART-puskuri ja loytyi: ")
	debug(serData)
	
	#tarkastetaan data rate eli kaytossa oleva Spreading Factor
	# komennolla: "lora get 2"
	# Jos 0-2: max payload = 59
	# Jos 3: max payload = 123
	# Jos 4-7: max payload = 230
	return dataRate;

def LoraGetJoinState():
	LoraYhteysMuodostettu=False
	serData=ser.read(512); # Varmistetaan etta puskuri on tyhja
	debug("Tyhjennettiin UART-puskuri ja loytyi: ")
	debug(serData)
	joinStateStr="";
	serData=ATcommandLora(loraGetJoinStateCmd, writedelay);
	alkutagi="<VALUE>"
	lopputagi="</VALUE>"
	alkukohta=serData.find(alkutagi)
	loppukohta=serData.find(lopputagi)
	if (alkukohta>0 and alkukohta<loppukohta):
		joinStateStr=getMessageContent(serData, alkutagi, lopputagi);
	
	try:
		if joinStateStr=="Joined":
			LoraYhteysMuodostettu=True
			debug("Yhteys on muodostettu.")
		if joinStateStr=="Not Joined":
			LoraYhteysMuodostettu=False
			debug("Ei viela Lora yhteytta. Aja: lora join -komento.")
	except:
		joinStateStr="Error"
		LoraYhteysMuodostettu=False
	debug("Saatiin joinState vastaus: "+str(joinStateStr));
	
	serData=ser.read(128); # Varmistetaan etta puskuri on tyhja
	debug("putsattiin puskuri ja loytyi")
	debug(serData)
	
	#tarkastetaan data rate eli kaytossa oleva Spreading Factor
	# komennolla: "lora get 2"
	# Jos 0-2: max payload = 59
	# Jos 3: max payload = 123
	# Jos 4-7: max payload = 230
	return LoraYhteysMuodostettu;

			
def LoraSend(viestidata):
	if True: # varmistetaan aina radion valmiustila ennen viestin lahettamista
		radioValmiina=False;
		radioValmiina=LoraRadioTestOK();
		if not radioValmiina:
			LoraInitAll();
	palvelimenVastaus="";
	# check viestidata ok
	ehto=-1;
	bufferTooLarge=-1;
	loraLaskuri=0;
	sendFailedCounter=0;
	# Viestidata lainausmerkkeihin
	# TODO - tarvitaanko sarjaportille eri viive-asetus?
	reply=ATcommandLora('lora send "'+viestidata+'" 1 1', loracomdelay);
	palvelimenVastaus=reply;
	ehto=palvelimenVastaus.find('LoRa RX Complete Event');
	alkutagi="<INCOMINGDATA>";   # <INCOMINGDATA>Viestilaitteelle1</INCOMINGDATA>
	lopputagi="</INCOMINGDATA>";
		
	# debug("palvelimen koko vastaus: " + str(reply));
		
	while ehto==-1: # RX ei ole viela kuitattu UARTin kautta
		debug("ehto: "+str(ehto));
		loraLaskuri+=1;
		debug("loraLaskuri: "+str(loraLaskuri));
		bufferTooLarge=palvelimenVastaus.find('730E');
		if loraLaskuri<3:
			time.sleep(loracomdelay);  # odotetaan yhteensa: 3 x loracomdelay eli 30 s # ei turhaa 4. kertaa
		palvelimenVastaus=ser.read(512); # Varmistetaan etta puskuri on tyhja
		ehto=palvelimenVastaus.find('LoRa RX Complete Event');
		if loraLaskuri==3 and ehto==-1:
			debug("LoRa viestin lahettaminen epaonnistui - {0} kertaa perakkain. Viesti jaa loopissa lahettamatta. Kutsuva funktio reagoi kommunikaatiovirheeseen.".format(loraLaskuri));
			palvelimenVastaus="RX ERROR"; # palvelin ei vastannut, vastaus "RX error" tulkitaan kutsuvalla tasolla kommunikaatiovirheeksi
			ehto=-2;
		if bufferTooLarge!=-1:
			debug("Lahetettava viesti on liian suuri sallittuun pakettikokoon nahden. Max-viestikoko riippuu DataRatesta. Virhekoodi 730E - Buffer too Large."); # ongelma korjattu - tata virhetta ei pitaisi enaa tulla
			palvelimenVastaus="RX ERROR"; # ei voitu lahettaa, liian suuri puskuri
			ehto=-3;
		
	# tanne tullaan, jos ehto on toteutunut
	
	if ehto>=0:
		debug("RX-kuittaus havaittu kohdassa - ehto: "+str(ehto));
		palvelimenVastaus=getMessageContent(palvelimenVastaus, alkutagi, lopputagi);
		debug("palvelimenVastaus parsittuna on: " +str(palvelimenVastaus));
	
	return palvelimenVastaus

def simpleTests():
	debug("Ajetaan testikomentoja laitteen toimivuuden testaamiseksi.\n");
	reply=ATcommandLora('ATI 1', tinydelay)
	reply=ATcommandLora('ATI 3', tinydelay)
	reply=ATcommandLora('AT+dir', tinydelay)

def LoraInit():
	reply=""
	reply2="error. Not connected"
	debug("Initializing LoRa connection\n");
	# check everything ok
	ehto=-1;
	error=0;
	loraLaskuri=0;
	joinFailedCounter=0;
	moodi=0;
	dataRate=0;
	loraJoinState=False; # 
	moodi=testRM186() # po 2 # ohitetaan lora join, jos yhteys on jo muodostettu. Voidaan poistaa jos halutaan aina luoda uusi yhteys.
	if moodi==2:
		debug("Jouko softa on ajossa. Kysytaan yhteyden tila eli joinState.")
		
		loraJoinState=LoraGetJoinState(); # kysytaan onko jo liitytty verkkoon "lora get 3" --> <VALUE>Not Joined</VALUE> tai <VALUE>Joined</VALUE>
		# dataRate=LoraGetDataRate(); # po. 0 alussa
		# kysytaan onko jo liitytty verkkoon "lora get 3" --> <VALUE>Not Joined</VALUE> tai <VALUE>Joined</VALUE>
		
	if loraJoinState:
		# Yhteys on jo ok. Tarkastetaan viela datarate.
		dataRate=LoraGetDataRate(); # po. 0 alussa
		debug("Datarate on : " + str(dataRate) + " , siis yhteys on jo kaynnissa.");
		reply='Successfully joined the LoRa'; # kerrotaan jatkolle, etta yhteys on ok
	# Send join request for gateway
	if moodi==2 and (not loraJoinState):
		reply=LoraJoin();
			
	ehto=reply.find('Successfully joined the LoRa');
	if ehto >0:
		reply2="OK"
		
	# loop to wait for LoRa connection
	while ehto==-1 and error==0:
		loraLaskuri+=1;
		time.sleep(lorajoinextradelay);
		if loraLaskuri==6:
			reply=LoraJoin();
			ehto=reply.find('Successfully joined the LoRa');
		debug(reply);
		debug("ehto: "+str(ehto));
		debug("loraLaskuri: " +str(loraLaskuri));
		if loraLaskuri==12:
			# jos yhteys ei muodostu noin minuutissa, niin resetoidaan ohjelmisto
			joinFailedCounter+=1;
			loraLaskuri=0;
			reply=softReset();
			reply=startJouko();
			reply=LoraJoin();
			ehto=reply.find('Successfully joined the LoRa');
		if joinFailedCounter==5:
			# jos yhteys ei muodostu noin minuutissa, niin resetoidaan radiolaite
			msg="Lora failed. Reset radio"
			debug(msg);
			error=10; # reset RM186
			return error
	return reply2
	
	
#######################################################################################
# ------------------------------- SERVER COMM --------------------------------------- #
#######################################################################################

def LairdJoukoInit(): # Normal Jouko Start 
	reply=100;
	reply=testRM186();
	# 1 = RM186 Is Waiting In AT CommandMode - #ehto1=reply.find('<RM186IsWaitingInATCommandMode>');
	# 2 = RM186 Is Running Jouko - # ehto2=reply.find('<RM186IsRunningJouko>');
	# 100 = jumissa
	if reply==100:
		debug("Laite on jumissa. Uudelleenkaynnistys on tarpeen.") # RESET kutsuvalla tasolla
	if reply==2:
		debug("RM186 ajaa jo Jouko-ohjelmistoa. Ohitetaan JoukoStart. Jatketaan yhteyden muodostamiseen.")
	if reply==1:
		UARTsyncLaird(); # debug("Synkronoidaan UART AT-komennoilla. Ei ehka pakollinen, mutta varmistaa toimivuuden. Kerran havaittu kaikuongelma ilman.")
		simpleTests(); # Katsotaan laitteen versio ja ajettavissa olevat ohjelmat.
		reply=startJouko(); # Jouko-softan start-komento
	return reply


def LairdDownAndUp(): # for demo-use
	debug("Suljetaan Jouko-softa ja resetoidaan laite.\n");
	reply=softReset();
	clearSerialBuffer();
	reply=UARTsyncLaird();
		

def LoraInitAll(): # turha
	debug("Alustetaan LoRa-radio kokonaisuudessaan.");
	reply1=LairdJoukoInit();
	while reply1==100:
		hardReset();
		reply1=LairdJoukoInit();
	reply=LoraInit(); # liity verkkoon
	while "error" in reply:
		hardReset();
		reply1=LairdJoukoInit();
		reply=LoraInit(); # liity verkkoon
		
def LoraRadioTestOK():
	debug("Valmistetaan, etta Lora-radio on ok.")
	testi=False
	dataRate=11
	# ajetaan testit
	reply=testRM186()
	if reply==2:
		debug("Jouko ajossa. OK.")
		
		loraJoinState=LoraGetJoinState(); # kysytaan onko jo liitytty verkkoon "lora get 3" --> <VALUE>Not Joined</VALUE> tai <VALUE>Joined</VALUE>
		if loraJoinState: # Yhteys on jo ok. Tarkastetaan viela datarate.
			dataRate=LoraGetDataRate();
		if dataRate>=0 and dataRate<11:
			debug("DataRate on OK.") 
			testi=True;
	else:
		debug("Radio ei OK. Tarvitaan RESET.")
		testi=False
	return testi;
	
