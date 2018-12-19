# pylint: disable=W0614

# viestinpurku.py - server message management
# - This program manages the use of protobuf messages used in communication between the control device and the server. The functions of the laiteviestit_pb2.py are used to encode and decode the protobuf messages.
# viestinpurku.py - palvelin viestien hallinta
# - Tama ohjelmakomponentti purkaa ja pakkaa ohjauslaitteen ja palvelimen valiset protobuf-rakenteiset viestit. Viestien pakkaamiseen ja purkamiseen kaytetaan laiteviestit_pb2.py-ohjelman funktioita.

from laiteviestit_pb2 import *
import base64
import re

def etsi_viesti(tuleva):
    viesti = re.findall(b"{([^}]*)}", tuleva)
    if viesti:
        return base64.b64decode(viesti[0])
    else:
        return None

def pakkaa_viesti_laitteelle(tyyppi, saapuva):
	viesti = ViestiLaitteelle()
	if tyyppi == "katkot":
		for katko in saapuva["katkot"]:
			uusi = viesti.katkot.katkot.add()
			uusi.katkoID = katko["katkoID"]
			uusi.laiteID = katko["laiteID"]
			uusi.alku = katko["alku"]
			uusi.loppu = katko["loppu"]
	elif tyyppi == "katkonestot":
		for katko in saapuva["katkonestot"]:
			uusi = viesti.katkonestot.katkonestot.add()
			uusi.katkoID = katko["katkoID"]
	elif tyyppi == "aikasynkLaitteelle":
		viesti.aikasynkLaitteelle.erotus = saapuva["aikasynk"]["erotus"]
	elif tyyppi == "sbUpdateStart":
		viesti.sbUpdateStart.numFiles = int(saapuva["sbUpdateStart"]["numFiles"])
	elif tyyppi == "sbUpdatePart":
		viesti.sbUpdatePart.num = str(saapuva["sbUpdatePart"]["num"])
		#viesti.sbUpdatePart.part = b"{" +base64.b64encode(saapuva["sbUpdatePart"]["part"])	+ b"}"
		part_str=saapuva["sbUpdatePart"]["part"]
		viesti.sbUpdatePart.part = (saapuva["sbUpdatePart"]["part"]).encode()
	elif tyyppi == "sbUpdateStop":
		viesti.sbUpdateStop.splitSize = int(saapuva["sbUpdateStop"]["splitSize"])
		viesti.sbUpdateStop.numFiles = int(saapuva["sbUpdateStop"]["numFiles"])
	raaka = viesti.SerializeToString()
	koodattu = b"{" + base64.b64encode(raaka) + b"}"
	return koodattu


def pakkaa_viesti(tyyppi, lahteva):
    viesti = ViestiLaitteelta()
    if tyyppi == "mittaukset":
        mittaukset = lahteva["mittaukset"]
        keskiarvot = []
        releOhjaukset = 0
        for i, mittaus in enumerate(mittaukset):
            (vaihe1KA,vaihe2KA,vaihe3KA,releOhjaus) = mittaus
            keskiarvot += [vaihe1KA, vaihe2KA, vaihe3KA]
            if releOhjaus:
                releOhjaukset |= 1<<i
        if "pituusMinuutteina" in lahteva:
            pituusMinuutteina = lahteva["pituusMinuutteina"]
            viesti.mittaukset.pituusMinuutteina = pituusMinuutteina
        for ka in keskiarvot:
            viesti.mittaukset.keskiarvot.append(ka)
        laiteID = lahteva["laiteID"]
        viesti.mittaukset.laiteID = laiteID
        aika = lahteva["aika"]
        viesti.mittaukset.aika = aika
        viesti.mittaukset.releOhjaukset = releOhjaukset
    if tyyppi == "aikasynk":
        print("OLLAAN aikasynkissa")
        print(viesti)
        viesti.aikasynkLaitteelta.laiteaika = lahteva["aikasynk"]["laiteaika"]; # edit 08.10.2018 add ["aikasynk"]
        print(viesti)
        if "syy" in lahteva["aikasynk"]: # edit 09.10.2018 - ei toimi, koska rakenne puuttuu
            pass;
            # viesti.aikasynkLaitteelta.syy = lahteva["aikasynk"]["syy"] ;
    raaka = viesti.SerializeToString()
    koodattu = b"{" + base64.b64encode(raaka) + b"}"
    return koodattu

def pura_viesti(tuleva):
    viesti = ViestiLaitteelle()
    etsitty = etsi_viesti(tuleva)
    if etsitty is not None:
        viesti.ParseFromString(etsitty)
    tyyppi = viesti.WhichOneof("viesti")
    if tyyppi == "katkot":
        katkot = []
        for katko in viesti.katkot.katkot:
            katkot.append({
                "katkoID": katko.katkoID,
                "laiteID": katko.laiteID,
                "alku": katko.alku,
                "loppu": katko.loppu
            })
        return {"katkot":katkot}
    elif tyyppi == "katkonestot":
        katkonestot = []
        for katkonesto in viesti.katkonestot.katkonestot:
            katkonestot.append({
                "katkoID": katkonesto.katkoID
            })
        return {"katkonestot":katkonestot}
    elif tyyppi == "aikasynkLaitteelle":
        return {"aikasynk": {
            #"erotus": viesti.aikasynkLaitteelle.aikasynkLaitteelle.erotus
            "erotus": viesti.aikasynkLaitteelle.erotus
        }}
    elif tyyppi == "sbUpdateStart":
        return {"sbUpdateStart": {
            #"numFiles": viesti.sbUpdateStart.sbUpdateStart.numFiles
            "numFiles": viesti.sbUpdateStart.numFiles
        }}
    elif tyyppi == "sbUpdatePart":
        return {"sbUpdatePart": {
            #"num": viesti.sbUpdatePart.sbUpdatePart.num,
            #"part": viesti.sbUpdatePart.sbUpdatePart.part
            "num": viesti.sbUpdatePart.num,
            "part": viesti.sbUpdatePart.part
        }}
    elif tyyppi == "sbUpdateStop":
        return {"sbUpdateStop": {
            "splitSize": viesti.sbUpdateStop.splitSize,
            "numFiles": viesti.sbUpdateStop.numFiles,
            "fileName": str(viesti.sbUpdateStop.fileName),
            "versioNumero": viesti.sbUpdateStop.versioNumero
        }}
    else:
        raise ValueError("Epakelpo viesti")
