#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################

# valvoja.py - control device operating watchdog
# valvoja.py - ohjauslaitteen toiminnan Watchdog

################################## Tarpeelliset Import ##########################################
import time;
import json;
import datetime;
import os; # set time

tarkastusloopinTiheys=1*60; # 1*60 # aika sekunteina eli tila luetaan x minuutin valein. Jos tila on muuttumaton 10 kertaa, resetoidaan laite.


time.sleep(200); #100 ### Odotetaan hieman, ettei paaohjelma kaynnisty taysin samaan aikaan.

with open('testiasetukset.json') as json_testi_settings_file:
	testiasetus	= json.load(json_testi_settings_file)

## Alustukset
os.system("cp initial.json ohjelmanTila.json"); # alustetaan status-tiedostoon
laskuri=0
epaonnistumiset=0;
status=0

def resetoiTietokone():
	import GPIOhallinta;
	# GPIOhallinta.vapautaIO();
	# GPIOhallinta.testaaGPIOmode();
	GPIOhallinta.alustaIO();
	GPIOhallinta.LED3vilkutus(20, 0.5);
	GPIOhallinta.resetSelf();

#jono = collections.deque('1234567890'); # luodaan alkutilan statuslista
jono = [1,2,3,4,5,6,7,8,9,10]; # luodaan alkutilan statuslista
	
while True:
	laskuri+=1;
	if laskuri>11000:
		laskuri=laskuri-10000
	time.sleep(tarkastusloopinTiheys)
	
	### Ladataan paaohjelman tila
	try:	
		with open('ohjelmanTila.json') as json_ohjelmanTila:
			paaohjelmanStatus = json.load(json_ohjelmanTila)
	except:
		epaonnistumiset+=1;
	try:
		### Kirjataan paaohjelman tila talteen
		status=paaohjelmanStatus['status']['koodi'];
		epaonnistumiset=0;
	except:
		epaonnistumiset+=1;	
	poistettuAlkio=jono.pop(0); # poistetaan listan ensimmainen elementti
	jono.append(status)# lisataan uusi status listaan viimeiseksi
	
	joukko = set(jono);
	joukonKoko=len(joukko)
	
	if joukonKoko==1:
		resetoiTietokone();
		
	if epaonnistumiset>5:
		resetoiTietokone();
	
