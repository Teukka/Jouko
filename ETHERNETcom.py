#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ETHERNETcom.py - Communicating through the device's built-in Internet connection
# - The device could also be used on the device via a pre-established internet connection. This program component defines the communication of the device through the existing Internet connection. An Internet connection can be, for example, a WLAN or other connection to a device.
# - Note! This component is intended for test use only. Continuous use of a fixed Internet connection would require a number of changes to your device to ensure its data security.
# ETHERNETcom.py - kommunikaatio laitteen valmiin internet-yhteyden kautta
# - Laitetta voitaisiin kayttaa myos laitteeseen valmiiksi luodun internetyhteyden kautta. Tassa ohjelmakomponentissa maaritellaan laitteen kommunikaatio valmiin olemassa olevan internet-yhteyden kautta. Internet-yhteys voi olla esimerkiksi, WLAN tai muu laitteeseen luotu yhteys. 
# - Huom! Tama komponentti on tarkoitettu vain testikayttoon. Kiintean Internet-yhteyden jatkuva kaytto vaatisi useita ohjelmallisia muutoksia laitteeseen sen tietoturvallisuuden varmistamiseksi.

import requests; # importing the HTTP requests library
# import time;
import base64;
import json;

# from types import SimpleNamespace # korvataan omalla, koska puuttuu Raspbianista
class SimpleNamespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        keys = sorted(self.__dict__)
        items = ("{}={!r}".format(k, self.__dict__[k]) for k in keys)
        return "{}({})".format(type(self).__name__, ", ".join(items))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


with open('asetukset.json') as json_general_settings_file:
	asetus	= json.load(json_general_settings_file)
with open('kommunikaatio.json') as json_com_settings_file:
	kommunikaatioasetus	= json.load(json_com_settings_file)
with open('testiasetukset.json') as json_testi_settings_file:
	testiasetus	= json.load(json_testi_settings_file)


debugON=testiasetus['test']['debugON'];# True; # kun 1, niin ei nayteta debug-funktion viesteja

nimi=kommunikaatioasetus['GPRS']['laite_nimi']; # basicAuth asetukset
pw=kommunikaatioasetus['GPRS']['laite_pw']; # basicAuth asetukset
postURL=kommunikaatioasetus['GPRS']['postURL']; # basicAuth asetukset

HTTPtimeout=5;

url=postURL;

getURL="jouko.smartip.cl:1880/sivu"

# tyhjia alustuksia
viesti=""
reply=""
msg=""
laskuri=0;

##################################################################################
## Perus funk
def debug(data):
	if debugON:
		print (str(data));

#################################################################################
## HTTP / GPRS kommunikaatio funktiot
	
def sendHTTPpost(viesti):
	credentials_str=str(nimi)+":"+str(pw);
	credentials_binary=credentials_str.encode('ascii') # 
	credentials_b64=(base64.b64encode(credentials_str.encode('ascii'))) # b'binary'
	credentials_utf=credentials_b64.decode("utf-8") # 'binary' # remove b'
	auth_credentials='Basic '+credentials_utf # 
	auth_header={'Authorization': 'Basic '+credentials_utf}	
	headers=auth_header

	merkkeja=len(viesti);
	debug("Lahetetaan viesti: "+str(viesti) + " ; Viestin datan pituus on: "+str(merkkeja)+" ; Viestin header-info on : "+str(headers));

	try:
		reply = requests.post(url, data=viesti, headers=headers, timeout=HTTPtimeout);
		debug("Palvelin vastasi: "+str(reply));
	except:
		replyDict = {'status_code':1234, 'text': 'HTTP post ei onnistunut.'}
		reply = SimpleNamespace(**replyDict)
		paluuviesti=reply.text;
	
	if reply.status_code==200:
		# debug ("Viesti meni perille");
		# debug("reply.text: " + str(reply.text));
		debug("reply.content: " + str(reply.content));
		debug("reply.status_code: " + str(reply.status_code));
		paluuviesti=reply.content
		#debug("paluuviesti: ")
		#debug(paluuviesti)
		errorState=False
	else:
		# debug("Viesti ei mennyt perille --> RX ERROR");
		paluuviesti=str(reply.status_code)
		errorState=True
	return paluuviesti,errorState;
