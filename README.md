# ha_ostrom
Integration Ostrom in to Home Assistant

only Playground!
Beginner Level Programming for Homeassistant#
Version 2.1


Path in Home Assistant 
/homeassistant/custom_components/ostrom

Man muss Kunde bei Ostrom sein
in der Web App account erstellen

Beschreibung der Web API https://docs.ostrom-api.io/reference/introduction

Zugang erstellen https://developer.ostrom-api.io/auth/login

dort hat man die Wahl zwischen Sandbox und Production - meine Software arbeitet mit Production Umgebung

Beim Anlegen erhält man eine Client ID und erzeugt dann ein Secret - beides wird benötigt

eintrag in configuration.yaml
```
ostrom:
  apiuser: "ostrom_user_id"
  apipass: "ostrom_secret"
```


 es werden 3 services erzeugt 
-   ostrom.get_price
	```
	Abfrage von Forcast Preisen maximal 36 Stunden in die Zukunft,
	Normal gibt es neue Daten nachmittags um 14 oder 15 Uhr
	Aufruf ohne Optionen
	im states ostrom.price was von der Api angelegt wird, Aktueller Strompreis in Cent
	attribute:
	average: durchschnittspreis in cent von den gelieferten  Daten
	low: 
		date: '2025-02-04T12:00:00.000Z'
		price: 29.33
		
 	low["date"] Uhrzeit vom nidrigsten Preis  
 	low["price"] der preis in cent zu dem zeitpunkt

 
	data: liste von forcast preisen jeweils mit
  		date "datum/uhrzeit"
  		price "centpreis zu dem zeitpunkt"
	
	```
	+	nachfolgende Services bemötigen ein Smartmeter mit ImSys 
	+	Datenübertragung - In der App muss ein Stundenverbrauch angezeigt
	+	werden - sonst liegen keine Daten vor und es gibt ein Abfragefehler
	
-   ostrom.get_power

	+ 	days_back
		* 	Optonal - Default ist 2 
	```
	Liefert den Stromverbrauch der vom Zähler übermittelt wurde - leider 
	sind die Werte erst mit verzögerung abrufbar, darum die 2 tage in die
	Vergangenheit
	mögliche Auswertungen für HA - unklar, da Sensordaten nur mit aktueller
	Zeit angelegt werden können.
	
	erzeugt ostrom.grid
		gesamt Verbrauch vom Tag ab 00:00 Uhr
		attribute
			Data		Stundenweise Liste
				date		datum/uhrzeit
				kWh		erfasster Stromverbrauch
				
	```

-	ostrom_cost
	+	ohne Option
	
	```
	Liefert Daten von aktueller Stunde 2 Tage in Vergangenheit
	erzeugt ostrom.cost
		berechnete Stromkosten der Stunde in Euro
		Attribute:
			price_data
				date		Datum/Uhrzeit 
				price	Strompres in Cent
			consum_data
				date		Datum/Uhrzeit
				kWh		Strombezug 
		
	```
	
Aktuell erforsche ich Möglichkeiten mit den Kostendaten etwas sinnvolles anfangen zu können.	
	
