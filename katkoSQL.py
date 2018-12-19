#!/usr/bin/env python
# -*- coding: utf-8 -*-

# katkoSQL.py – power interruption (break) management using SQL database
# - This program component includes all the functions used to control the power interruption database.
# katkoSQL.py - releiden katkojen hallinta SQL-tietokannan avulla
# - Tama ohjelmakomponentti sisaltaa kaikki katkotietokannan hallinnassa kaytettavat funktiot.

import sqlite3;
import threading;
import time;
import json;

with open('asetukset.json') as json_general_settings_file:
	asetus	= json.load(json_general_settings_file)

with open('kommunikaatio.json') as json_com_settings_file:
	kommunikaatioasetus	= json.load(json_com_settings_file)

with open('testiasetukset.json') as json_testi_settings_file:
	testiasetus	= json.load(json_testi_settings_file)

###### BT -configuraatio #####
omaLaiteID=kommunikaatioasetus['com']['omaLaiteID'];
# kytkinLaiteID voi olla tama laite tai BT-laite
BTlaiteID1=kommunikaatioasetus['com']['BTlaiteID1'];#5;
BTlaiteID2=kommunikaatioasetus['com']['BTlaiteID2'];#6;
BTlaiteID3=kommunikaatioasetus['com']['BTlaiteID3'];#7; # ylimaaraiset BTlaite-koodit voidaan asettaa samaksi kuin ID1
BTlaiteID4=kommunikaatioasetus['com']['BTlaiteID4'];#8;

debugON=testiasetus['test']['debugON'];# True; # kun 1, niin ei nayteta debug-funktion viesteja

import GPIOhallinta;

def debug(data):
	# Komento, jolla annetaan palautetta haluttuun kanavaan. 
	# Nyt tulostetaan data UARTiin.	
	if debugON:
		print (str(data));

############################## -- Katkojen hallinta -- ##############################
#viestiTyyppi=4; # katkoAlkaa viesti

global katko1SaieAjossaOdotus; katko1SaieAjossaOdotus=0;
global katko1SaieAjossaKatko; katko1SaieAjossaKatko=0;

# jos halutaan kaksi katkoa jonoon: # tuplataan katkojono - turha - ei tarpeen, koska tietokanta
global katko2SaieAjossaOdotus; katko2SaieAjossaOdotus=0;
global katko2SaieAjossaKatko; katko2SaieAjossaKatko=0;

def checkKatkoDataOK(katkoID, katkoLaiteID, katkonAlkuun, katkonKesto):
	check1=0;
	check2=0;
	check3=0;
	check4=0;
	testiTulos=0;
	if katkoID>0: # aika turha check, kun on jo int
		check1=1;
		# debug("katkoID on OK");
	if katkoLaiteID==omaLaiteID: #  ("checkataan ID on tama joko omaLaiteID tai BTlaiteID")
		check2=1;
		# debug("katkoLaiteID on OK");
	if katkoLaiteID==BTlaiteID1 or katkoLaiteID==BTlaiteID2 or katkoLaiteID==BTlaiteID3 or katkoLaiteID==BTlaiteID4: # onko BTlaite?
		check2=1;
		# debug("BT-katkoLaiteID on OK");
	if katkonAlkuun>0:
		check3=1;
		# debug("katkonAlkuun > 0");
	if katkonKesto>0:
		check4=1;
		# debug("katkonKesto > 0");
	testiTulos=check1*check2*check3*check4;
	return(testiTulos);


##################################### --------------------------------- SQL ------------------------- ########################
## SQL Katkotiedot-taulun hallinta

def avaaTietokanta():
	global conn;
	conn = sqlite3.connect('jouko.db')
	conn.commit();

def luoKatkotaulu(): # 1 CREATE TABLE - Taulun luominen
	global conn;
	c=conn.cursor()
	c.execute('''
		CREATE TABLE IF NOT EXISTS Katkotiedot (
		katkoID INTEGER NOT NULL,
		laiteID INTEGER NOT NULL,
		alku INTEGER NOT NULL,
		loppu INTEGER NOT NULL,
		aktiivinen BOOLEAN DEFAULT False)
	''');
	conn.commit();
	pass

def lisaaKatkotiedot(serverKatkoID, katkoLaiteID, katkonAlku, katkonLoppu, aktiivinen=False): # 2 INSERT INTO - Katkotiedon lisaaminen
	# debug("Lisataan katkotiedot tietokantaan")
	debug("Ajetaan SQL: INSERT INTO Katkotiedot VALUES ("+str(serverKatkoID)+", "+str(katkoLaiteID)+", "+str(katkonAlku)+", "+str(katkonLoppu)+", "+str(aktiivinen)+")") # SQL
	global conn;
	c=conn.cursor()
	# Todo Extra jos haluaa: CHECK jos katkoID vapaana AND ei aktiivinen? JOS EI vapaana -->  update. Ei tarpeen, silla palvelimella katkoID on aina uniikki.
	vapaana=True;
	if vapaana:
		c.execute('''
		INSERT INTO Katkotiedot (katkoID, laiteID, alku, loppu, aktiivinen) VALUES (?, ?, ?, ?, ?)
		''', (serverKatkoID, katkoLaiteID, katkonAlku, katkonLoppu, aktiivinen)
		); # SQL
	if (not vapaana): # zzzzz sovita UPDATE katkoID:n mukaan
		c.execute('''
		UPDATE Katkotiedot (katkoID, laiteID, alku, loppu, aktiivinen) VALUES (?, ?, ?, ?, ?)
		''', (serverKatkoID, katkoLaiteID, katkonAlku, katkonLoppu, aktiivinen)
		); # SQL
	conn.commit();
	pass;

def merkitseKatkoAktiiviseksi(alkavanKatkonID):
	debug("Merkitaan katko aktiiviseksi, kun siita on luotu katkosaie.")
	# jos katkoja loytyi, merkitaan ne aktiivisiksi # 7 UPDATE Katkotiedot SET aktiivinen - saie luodaan
	aktiivinenArvo=1;
	katkoTuple=(aktiivinenArvo, alkavanKatkonID)
	global conn;
	c=conn.cursor()
	c.execute('''
	UPDATE Katkotiedot SET aktiivinen=? WHERE katkoID=?;		
	''', katkoTuple); # SQL
	conn.commit();
	debug("Katko on merkitty aktiiviseksi.")

def merkitseKatkoPassiiviseksi(alkavanKatkonID):
	aktiivinenArvo=0;
	katkoTuple=(aktiivinenArvo, alkavanKatkonID)
	global conn;
	c=conn.cursor()
	c.execute('''
	UPDATE Katkotiedot SET aktiivinen=? WHERE katkoID=?;		
	''', katkoTuple); # SQL
	conn.commit();
	debug("Katko on merkitty EI-aktiiviseksi.")

	
def poistaVanhentuneetKatkot(): # 4 DELETE FROM - Katkotiedot poistetaan, katkon loppuessa tai vanha katkotark.
	# debug("Poistetaan vanhentuneet katkot, joiden loppuaika on menneisyydessa.")
	aikaleimaNyt = int(round(time.time() )); # aikaleima sekunteina
	# SELECT * FROM Katkotiedot WHERE loppu<AikaleimaNyt; # 3 SELECT * FROM _ WHERE - Peruskysely, vanhentuneita katkoja (turha)
	global conn;
	c=conn.cursor()
	c.execute('''
	DELETE FROM Katkotiedot WHERE loppu<?
	''', (aikaleimaNyt,));
	conn.commit();
	pass;

def poistaYksiKatkotieto(poistettavaKatkoID): # 5 DELETE FROM - Katkotiedot poistetaan, estettaessa katko katkoID:lla (palvelin)

	debug("Valinnainen TODO. Voitaisiin toteuttaa, mutta ei-toivottu ominaisuus: Jos katkoSaie on jo ajossa, niin katkaistaanko saie? Ei.")
	##for row in c.execute('''
	##	SELECT * FROM Katkotiedot WHERE katkoID=? AND aktiivinen=1
	##	''', (poistettavaKatkoID,)): # SQL
	##	debug ("row: ")
	##	debug (row)
		# kerataan datat muuttujiin ja luodaan katkoSaie
	##	alkavanKatkonID=row[0];
	##	katkoLaiteID=row[1];
	##	katkonAlku=row[2];
	##	katkonLoppu=row[3];	
	##	debug ("alkavanKatkonID on:" + str(alkavanKatkonID)+" ; katkoLaiteID on: " + str(katkoLaiteID) + " ; katkonAlku: "+str(katkonAlku)+" ; katkonLoppu: " +str(katkonLoppu))
					
	##	if katkoLaiteID==omaLaiteID: # TODO debug ("checkataan ID on tama joko omaLaiteID tai BTlaiteID")
	##		debug("Checkattiin ID ja se on oma laiteID")

	debug("DELETE FROM Katkotiedot WHERE katkoID={0}".format(poistettavaKatkoID)) # SQL
	global conn;
	c=conn.cursor()
	c.execute('''
	DELETE FROM Katkotiedot WHERE katkoID=?
	''', (poistettavaKatkoID,)); # SQL
	conn.commit();
	
	pass;

def kaynnistaAjankohtaisetKatkot(katkoSaikeenLuomisenEnnakko=360): # 6 SELECT * FROM  - Peruskysely, katkoja esim. 5 minuutin sisalla (katkoSaikeenLuomisenEnnakko) – luo katko
	# debug("Luodaan katkosaikeet katkoista, joiden alkamisaikaan on alle 6 minuuttia tai ovat jo alkaneet, mutta loppuaika ei ole menneisyydessa.")
	#  TABLE Katkotiedot (katkoID INTEGER PRIMARY KEY NOT NULL, laiteID INTEGER NOT NULL, alku TIME NOT NULL, loppu TIME NOT NULL, aktiivinen BOOLEAN DEFAULT False)
	
	aikaleimaNyt = int(round(time.time() )); # aikaleima sekunteina
	vertailuAikaleima = int(aikaleimaNyt+katkoSaikeenLuomisenEnnakko); # vertailuaikaleima sekunteina, jossa katkoSaikeenLuomisenEnnakko on ennakointiaikavali sekunteina
	global conn;
	c=conn.cursor()  # SQL ## TURHA: ## IF EXISTS (SELECT * FROM Katkotiedot WHERE alku<? AND aktiivinen=0 AND loppu>?)
	
	for row in c.execute('''
		SELECT * FROM Katkotiedot WHERE alku<? AND aktiivinen=0 AND loppu>?
		''', (vertailuAikaleima, aikaleimaNyt)): # SQL
		debug ("row: ")
		debug (row)
		# kerataan datat muuttujiin ja luodaan katkoSaie
		alkavanKatkonID=row[0];
		katkoLaiteID=row[1];
		katkonAlku=row[2];
		katkonLoppu=row[3];	
		debug ("alkavanKatkonID on:" + str(alkavanKatkonID)+" ; katkoLaiteID on: " + str(katkoLaiteID) + " ; katkonAlku: "+str(katkonAlku)+" ; katkonLoppu: " +str(katkonLoppu))
					
		if katkoLaiteID==omaLaiteID: # TODO debug ("checkataan ID on tama joko omaLaiteID tai BTlaiteID")
			debug("Checkattiin ID ja se on oma laiteID")
			katkonKesto=katkonLoppu-katkonAlku;
			katkonAlkuun=katkonAlku-aikaleimaNyt;
			luoTulevaKatko(alkavanKatkonID, katkoLaiteID, katkonAlkuun, katkonKesto); # tuotava alku ja loppu, jos BT-laite		
			merkitseKatkoAktiiviseksi(alkavanKatkonID);
		
		if katkoLaiteID==BTlaiteID1 or katkoLaiteID==BTlaiteID2 or katkoLaiteID==BTlaiteID3 or katkoLaiteID==BTlaiteID4: # onko BTlaite?		
			luoTulevaKatkoBT(alkavanKatkonID, katkoLaiteID, katkonAlku, katkonLoppu);
			merkitseKatkoAktiiviseksi(alkavanKatkonID);
			
#	if result.fetchone()[0]:
#		c=conn.cursor()
#		result = c.execute('''
#		SELECT * FROM Katkotiedot WHERE alku<? AND aktiivinen=0 AND loppu>?
#		''', (vertailuAikaleima, aikaleimaNyt)); # SQL
#		resultList=result.fetchall();
		#conn.commit();
	pass;
	
def tarkastaKatkotaulu(katkoSaikeenLuomisenEnnakkoSekunteina=120): # SQL
	# SELECT * FROM Katkotiedot WHERE loppu<AikaleimaNyt; 
	debug("--------- Tarkastetaan katkotaulu ----------")
	# debug("Tarkastetaan katkotaulu eli: Poistetaan vanhentuneet katkot ja kaynnistetaan ajankohtaiset katkot.")
	poistaVanhentuneetKatkot();
	kaynnistaAjankohtaisetKatkot(katkoSaikeenLuomisenEnnakkoSekunteina);
	# debug("----------------------------------------------------------------------")
	# Poistetaan ensin vanhentuneet katkot - Katkotiedot poistetaan, katkon loppuessa tai vanha katkotark.


########################### UUDET katkosaikeet ############################################
class katkoTulossa(threading.Thread): # saie tulevan katkon ajastamiseksi ja lopettamiseksi
	def __init__(self, katkoTulossaTiedot, kesto1, kesto2):
		super(katkoTulossa, self).__init__()
		self.viesti = katkoTulossaTiedot # turha, jos ei valiteta muita tietoja
		self.katkonAlkuun = kesto1
		self.katkonLoppuun = kesto2
		debug ("Saie init - Katkon alkuun on aikaa:" + str(kesto1))
		debug ("Saie init - Katkon alusta loppuun :" + str(kesto2))
	def run(self):
		debug (self.viesti)
		debug ("Katkon alkuun on alle 6 minuuttia. Odotetaan katkon alkamista.")
		debug("Odotettava aika on: " + str(self.katkonAlkuun) + " sekuntia")
		time.sleep(self.katkonAlkuun)
		debug ("Katko on alkaa. Rele avataan.")
		GPIOhallinta.avaaRele()
		time.sleep(self.katkonLoppuun)
		debug ("Katko loppuu. Rele suljetaan takaisin.")
		GPIOhallinta.suljeRele()
		
# maaritellaan saikeille otetustiedot, jotta voidaan tarkistaa, onko se ajossa.

def luoKatkoSaie(katkonAlkuun, katkonKesto): # voidaan luoda useita katkoja.
	#uusi versio
	saieA = katkoTulossa('Katko tiedot. Valitetaan saikeelle.',katkonAlkuun,katkonKesto)
	saieA.start()

def luoTulevaKatko(katkoID, katkoLaiteID, katkonAlkuun, katkonKesto): # tuotava alku ja loppu, jos BT-laite
	debug("luoTulevaKatko - Luodaan katko - katkottava laite on tama laite: " + str(omaLaiteID) + "; katkonAlkuun:" + str(katkonAlkuun)+"; katkonKesto: "+str(katkonKesto));
	luoKatkoSaie(katkonAlkuun, katkonKesto);
	debug("Luodaan oma saikeensa tarkkailemaan alkavaa katkoa ja katkon alettua tarkkailemaan loppuvaa katkoa.");

def BTkatkoSend(katkoID, katkoLaiteID, katkonAlku, katkonLoppu):
	# zzz TODO BT com send katko
	debug("Tarkastetaan onko maaritelty BT-laite: " +str(katkoLaiteID))
	debug("Lahetetaan katko - katkottava BT-laite: " + str(katkoLaiteID) + "; katkonAlku:" + str(katkonAlku)+"; katkonLoppu: "+str(katkonLoppu));

def BTkatkoReceive(katkoID, katkoLaiteID, katkonAlku, katkonLoppu):
	# TODO zzz pohdittava BT-laitteen toiminta
	debug("Tama laite on katkottava BT-laite: " + str(katkoLaiteID) + "; katkonAlku:" + str(katkonAlku)+"; katkonLoppu: "+str(katkonLoppu));
	#luodaan katko - saatiinko aika katkon alkuun ? jep
	lisaaKatkotiedot(katkoID, katkoLaiteID, katkonAlku, katkonLoppu, False)
	tarkastaKatkotaulu()
	
	
def luoTulevaKatkoBT(katkoID, katkoLaiteID, katkonAlku, katkonLoppu): # tuotava alku ja loppu, jos BT-laite
	debug("Katkottava laite on mahdollisesti BT-laite, koska tultiin tahan. Tarkastetaan katkotiedot:")
	debug("TODO tassa tarkastetaan BT-laitteen tiedot. Ja jos oikein, niin lahetetaan BT-viesti");
	## TODO zzzz tarkista on katkoLaiteID lainkaan maaritelty.
	if BTlaiteID1==katkoLaiteID: # voidaan vertailla laite kerrallaan, koska BT-laitteita on 0-4 kpl
		BTkatkoSend(katkoID, katkoLaiteID, katkonAlku, katkonLoppu);
	if BTlaiteID2==katkoLaiteID: # 
		BTkatkoSend(katkoID, katkoLaiteID, katkonAlku, katkonLoppu);
	if BTlaiteID3==katkoLaiteID: # 
		BTkatkoSend(katkoID, katkoLaiteID, katkonAlku, katkonLoppu);
	if BTlaiteID4==katkoLaiteID: # 
		BTkatkoSend(katkoID, katkoLaiteID, katkonAlku, katkonLoppu);
		# TODO korjaa BT-versio
	debug("BT-viesti lahetetty.");

def suljeTietokanta():
	conn.close;
	
# testataan tietokantaan
#avaaTietokanta()
#luoKatkotaulu()

#lisaaKatkotiedot(3,4,1526650048,1526650048,False)
#lisaaKatkotiedot(4,5,1526648899,1526648912)


# poistaVanhentuneetKatkot();
#merkitseKatkoAktiiviseksi(3);
# kaynnistaAjankohtaisetKatkot();

# tarkastaKatkotaulu();

#luoTulevaKatko(4,5,5,10)
#luoTulevaKatkoBT(5,5,1526648399,1526648412)