# ha_ostrom
Integration Ostrom in to Home Assistant

Beta Version!
Beginner Level Programming for Homeassistant#
Version 2.2


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
optionale Angaben:
```

  price_now: "name"	Erzeugt sensor.name als state_class: total, unit_of_measurement: EUR/kWh, device_class: monetary
			Aktueller Strompreis in EUR; wird von Recorder verarbeitet und landet in der History von HA
			ohne angabe der Option kein Sensor.
  supply_past: "Verbrauchszähler kWh Name"
			Erzeugt ein Sensor der den Stromverbrauch aufzählt, allerdings um 2 Tage verzögert :-(
                        state_class: total, unit_of_measurement: EUR, device_class: monetary, imsys_date: datum der messung
			Vorraussetzung IMSYS liefert Daten und Service - service ostrom.get_cost muss Stündlich Aufgerufen werden

  price_past: "Kostenzähler EUR Name"
			Erzeugt ein Sensor der die Kosten aufzählt (Bezug in kWh * Strompreis kWh/EUR zu dem Zeitpunkt)
   			state_class: total, unit_of_measurement: EUR, device_class: monetary, imsys_date: DateTime
			auch hier IMSYS Datenlieferung vorraussetzung; service ostrom.get_cost muss Stündlich Aufgerufen werden
```


 es werden 4 services erzeugt 
-   ostrom.get_price
	```
	Abfrage von Forcast Preisen maximal 36 Stunden in die Zukunft,
	Normal gibt es neue Daten nachmittags um 14 oder 15 Uhr
	Aufruf ohne Optionen - muss Stündliche aufgerufen werden
	im states ostrom.price was von der Api angelegt wird, Aktueller Strompreis in Cent
	attribute:
	average: durchschnittspreis in cent von den gelieferten  Daten
	low: 
		date: 'Zeitpunkt des günstigsten Strompreises'
		price: 'der dann gültige Preis in Cent' 
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
	Zeit angelegt werden können. Sensordaten In Vergangenheit anlegen gab es mal ein Request zu - wird nicht umgesetzt.
	
	erzeugt ostrom.grid
		gesamt Verbrauch vom Tag ab 00:00 Uhr
		attribute
			Data		Stundenweise Liste
				date		datum/uhrzeit
				kWh		erfasster Stromverbrauch
				
	```

-	ostrom_cost
	
	```
	Liefert Daten von aktueller Stunde 2 Tage in Vergangenheit
	erzeugt ostrom.cost
		berechnete Stromkosten der Stunde in Euro
		Attribute:
			price_data
				date		Datum/Uhrzeit 
				price		Strompres in Cent
			consum_data
				date		Datum/Uhrzeit
				kWh		Strombezug
 
		
	```
-	reset_meter
		Setzt Kostenzähler und Verbrauchszähler auf Null - nett für Monatsberechnung
 		ansonsten für Mehr in HACS gibts den "energy_meter" der kann als Tarifeingang ein Sensor nutzen.
 		Der von HA kann nur feste Tarife - für Dynamische Tarife unbrauchbar.
 	
Aktuell teste ich die Software - aber kann man mit arbeiten (finde ich) :-).	
Falls einer noch kein Ostrom Kunde ist unter Promo.text 
ist mein Promocode den man bei Neuvertrag angeben kann.
	
